from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from .records import ArtifactReference, TestRunRecord


class CurrentTestReportBuilder:
    def __init__(self, poc_root: Path) -> None:
        self.poc_root = poc_root
        self.current_reports_dir = poc_root / "reports" / "current"
        self.current_generated_dir = self.current_reports_dir / "generated"

    def _write_text(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _relative(self, path: Path) -> str:
        return str(path.relative_to(self.poc_root)).replace("\\", "/")

    def _benchmark_history(self, records: list[TestRunRecord]) -> list[tuple[str, float, float | None]]:
        rows: list[tuple[str, float, float | None]] = []
        for record in records:
            value = record.performance_summary.get("primary_metric_ms_per_step")
            normalized = record.projection_summary.get("normalized_ms_per_full_complexity")
            if value is None:
                continue
            rows.append((record.timestamp_utc, float(value), float(normalized) if normalized is not None else None))
        return rows

    def _svg_line_plot(self, path: Path, title: str, series: list[tuple[str, float]], y_label: str) -> None:
        width = 960.0
        height = 420.0
        margin = 70.0
        plot_width = width - 2 * margin
        plot_height = height - 2 * margin
        ys = [value for _, value in series] or [0.0]
        y_min = min(ys)
        y_max = max(ys)
        if y_min == y_max:
            y_min -= 1.0
            y_max += 1.0

        def x_for(index: int) -> float:
            if len(series) <= 1:
                return margin + plot_width / 2.0
            return margin + index / (len(series) - 1) * plot_width

        def y_for(value: float) -> float:
            return height - margin - (value - y_min) / (y_max - y_min) * plot_height

        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">',
            '<rect width="100%" height="100%" fill="white" />',
            f'<text x="40" y="34" font-size="22">{html.escape(title)}</text>',
            '<text x="40" y="56" font-size="14">Generated from append-only archival history.</text>',
            f'<line x1="{margin}" y1="{height-margin}" x2="{width-margin}" y2="{height-margin}" stroke="black" />',
            f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height-margin}" stroke="black" />',
            f'<text x="12" y="{margin}" font-size="12">{html.escape(y_label)}</text>',
        ]
        points: list[str] = []
        for index, (_timestamp, value) in enumerate(series):
            x = x_for(index)
            y = y_for(value)
            points.append(f"{x:.2f},{y:.2f}")
            lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4.5" fill="#1f77b4" />')
            lines.append(f'<text x="{x-18:.2f}" y="{height-margin+20:.2f}" font-size="10">{index+1}</text>')
        if points:
            lines.append(f'<polyline fill="none" stroke="#1f77b4" stroke-width="2" points="{" ".join(points)}" />')
        lines.append(f'<text x="{width-240}" y="{margin+10}" font-size="12">min={y_min:.4f}</text>')
        lines.append(f'<text x="{width-240}" y="{margin+26}" font-size="12">max={y_max:.4f}</text>')
        lines.append('</svg>')
        self._write_text(path, "\n".join(lines))

    def build(self, *, current_record: TestRunRecord, history: list[TestRunRecord]) -> list[ArtifactReference]:
        self.current_generated_dir.mkdir(parents=True, exist_ok=True)
        benchmark_history = self._benchmark_history(history + [current_record])

        raw_plot_path = self.current_generated_dir / "raw_performance_over_time.svg"
        raw_series = [(timestamp, value) for timestamp, value, _normalized in benchmark_history]
        if raw_series:
            self._svg_line_plot(raw_plot_path, "Raw performance vs time", raw_series, "ms per step")

        apples_plot_path = self.current_generated_dir / "apples_to_apples_performance.svg"
        compatible_rows: list[tuple[str, float]] = []
        compatible_ids = set(current_record.comparison_summary.get("compatible_run_ids", []))
        for record in history:
            if record.run_id in compatible_ids and record.performance_summary.get("primary_metric_ms_per_step") is not None:
                compatible_rows.append((record.timestamp_utc, float(record.performance_summary["primary_metric_ms_per_step"])))
        if current_record.performance_summary.get("primary_metric_ms_per_step") is not None:
            compatible_rows.append((current_record.timestamp_utc, float(current_record.performance_summary["primary_metric_ms_per_step"])))
        if compatible_rows:
            self._svg_line_plot(apples_plot_path, "Apples-to-apples benchmark trend", compatible_rows, "ms per step")

        projection_plot_path = self.current_generated_dir / "complexity_normalized_projection.svg"
        projection_series = [(timestamp, normalized) for timestamp, _raw, normalized in benchmark_history if normalized is not None]
        if projection_series:
            self._svg_line_plot(
                projection_plot_path,
                "Complexity-normalized projected full-complexity ms/step",
                projection_series,
                "normalized ms/step",
            )

        revalidated_suite_ids: list[str] = []
        new_suite_ids: list[str] = []
        previous_suite_ids = {suite.suite_id for record in history for suite in record.suite_results}
        for suite in current_record.suite_results:
            if suite.suite_id in previous_suite_ids:
                revalidated_suite_ids.append(suite.suite_id)
            else:
                new_suite_ids.append(suite.suite_id)

        summary_lines = [
            "# Current pyAIGameEngine Test Report",
            "",
            f"Generated from archival test data on {datetime.utcnow().isoformat(timespec='seconds')}Z.",
            "",
            "## 1. Human-oriented consumer summary of current test data",
            "",
            f"- Current run ID: `{current_record.run_id}`",
            f"- Timestamp (UTC): `{current_record.timestamp_utc}`",
            f"- Workspace version: `{current_record.workspace_version}` | POC version: `{current_record.poc_version}`",
            f"- Execution mode: `{current_record.execution_mode}` | Gate context: `{current_record.gate_context}`",
            f"- Suite selection: {', '.join(current_record.suite_selection)}",
            f"- Summary of re-validation of previous success/failure metrics: {', '.join(revalidated_suite_ids) if revalidated_suite_ids else 'No prior matching suite IDs in archive.'}",
            f"- Summary of new success/failure metrics: {', '.join(new_suite_ids) if new_suite_ids else 'No newly introduced suite IDs in this run.'}",
            f"- Validation summary: passed={current_record.validation_summary.get('checks_passed', 0)} failed={current_record.validation_summary.get('checks_failed', 0)} skipped={current_record.validation_summary.get('checks_skipped', 0)} overall_status={current_record.validation_summary.get('overall_status', 'unknown')}",
            "",
            "### Performance Tests and Results",
            "",
        ]
        perf = current_record.performance_summary
        if perf.get("primary_metric_ms_per_step") is not None:
            summary_lines.extend(
                [
                    f"- Primary benchmark metric: `{perf['primary_metric_ms_per_step']:.6f} ms/step`",
                    f"- Backend: `{perf.get('backend_label', 'unknown')}`",
                    f"- Benchmark family: `{perf.get('comparison_key', {}).get('benchmark_family_id', 'unknown')}`",
                    f"- Bodies / steps: `{perf.get('comparison_key', {}).get('bodies', 'n/a')} / {perf.get('comparison_key', {}).get('steps', 'n/a')}`",
                    f"- Compatible prior runs found: `{current_record.comparison_summary.get('compatible_count', 0)}`",
                    f"- Delta vs latest compatible run: `{current_record.comparison_summary.get('delta_ms_per_step_vs_latest_compatible')}` ms/step",
                ]
            )
        else:
            summary_lines.append("- No benchmark metric was recorded in the current run.")

        summary_lines.extend(
            [
                "",
                "### Visualization of Tests",
                "",
                "- Raw performance plot: `reports/current/generated/raw_performance_over_time.svg`",
                "- Apples-to-apples plot: `reports/current/generated/apples_to_apples_performance.svg`",
                "- Projection plot: `reports/current/generated/complexity_normalized_projection.svg`",
            ]
        )
        benchmark_snapshot_refs = [artifact for artifact in current_record.artifact_references if artifact.artifact_type == "svg_snapshot"]
        if benchmark_snapshot_refs:
            snapshot_ref = benchmark_snapshot_refs[0]
            summary_lines.extend(
                [
                    f"- Dynamic simulation snapshot: `{snapshot_ref.relative_path}`",
                    "- Snapshot significance: this render captures the final benchmark-frame spatial distribution of bodies and distinguishes agent bodies from non-agent bodies so later regressions in geometry or broad motion can be visually spotted.",
                ]
            )

        summary_lines.extend(
            [
                "",
                "## 2. Numerical and visual comparison between current and previous performance and guidance toward future performance",
                "",
                "- Raw performance vs time uses all archival benchmark runs found in `artifacts/test/archive/test_run_archive.jsonl`.",
                "- Apples-to-apples comparison uses exact compatibility-key matches on benchmark family, backend, scenario bundle, mode, bodies, steps, feature families, packet modes, and seed policy.",
                f"- Current complexity fraction: `{current_record.projection_summary.get('current_complexity_fraction')}`",
                f"- Complexity-normalized projected full-complexity metric: `{current_record.projection_summary.get('normalized_ms_per_full_complexity')}` ms/step",
                f"- Projected full-complexity steps/sec estimate: `{current_record.projection_summary.get('projected_steps_per_second_at_full_complexity')}`",
            ]
        )
        delta_pct = current_record.comparison_summary.get("delta_percent_vs_latest_compatible")
        if delta_pct is None:
            guidance = "No prior apples-to-apples run exists yet, so this run becomes the initial trend anchor for its comparison key."
        elif delta_pct <= -5.0:
            guidance = "The current apples-to-apples point improved materially. Preserve the same comparison key on the next run to confirm the gain is stable."
        elif delta_pct >= 5.0:
            guidance = "The current apples-to-apples point worsened materially. The next pass should inspect whether the change came from real engine cost, added instrumentation, or a temporary non-representative stage."
        else:
            guidance = "The current apples-to-apples point stayed near the previous comparable run. Continue building the archival series before drawing stronger conclusions."
        summary_lines.append(f"- Guidance toward future performance: {guidance}")

        summary_lines.extend(
            [
                "",
                "## 3. Appendix",
                "",
                "### Current state of development (implemented vs unimplemented)",
                "",
                f"- Implemented: {', '.join(current_record.development_state_summary.get('implemented_components', []))}",
                f"- Unimplemented: {', '.join(current_record.development_state_summary.get('unimplemented_components', []))}",
                f"- Current limitations: {', '.join(current_record.development_state_summary.get('current_limitations', []))}",
                "",
                "### Table of test parameters used",
                "",
                "| Parameter | Value |",
                "|---|---|",
            ]
        )
        for key, value in sorted(current_record.parameter_bundle.items()):
            summary_lines.append(f"| {key} | {value} |")

        summary_lines.extend(
            [
                "",
                "### Brief justification of assumptions made",
                "",
                "| Assumption | Justification |",
                "|---|---|",
            ]
        )
        for component in current_record.projection_summary.get("components", []):
            summary_lines.append(
                f"| {component['component_id']} | weight={component['target_weight']}, realization={component['current_realization_fraction']}; {component['rationale']} |"
            )

        summary_lines.extend(
            [
                "",
                "### Compatibility notes for trend comparison",
                "",
                f"- Comparison key: `{current_record.performance_summary.get('comparison_key', {})}`",
                f"- Compatible prior run IDs: {current_record.comparison_summary.get('compatible_run_ids', [])}",
                "",
                "### Artifact list",
            ]
        )
        for artifact in current_record.artifact_references:
            summary_lines.append(f"- `{artifact.relative_path}` — {artifact.description}")

        markdown_text = "\n".join(summary_lines) + "\n"
        markdown_path = self.current_reports_dir / "current_test_report.md"
        self._write_text(markdown_path, markdown_text)

        html_text = "".join(
            [
                "<html><head><meta charset='utf-8'><title>pyAIGameEngine current test report</title></head><body>",
                "<pre>",
                html.escape(markdown_text),
                "</pre></body></html>",
            ]
        )
        html_path = self.current_reports_dir / "current_test_report.html"
        self._write_text(html_path, html_text)

        artifacts = [
            ArtifactReference(
                artifact_type="current_report_markdown",
                relative_path=self._relative(markdown_path),
                description="Regenerated current human-readable test report in Markdown.",
                producer="current_report_builder",
            ),
            ArtifactReference(
                artifact_type="current_report_html",
                relative_path=self._relative(html_path),
                description="Regenerated current human-readable test report in HTML.",
                producer="current_report_builder",
            ),
        ]
        for plot_path, description in [
            (raw_plot_path, "Raw performance vs time plot."),
            (apples_plot_path, "Apples-to-apples comparison plot."),
            (projection_plot_path, "Complexity-normalized projection trend plot."),
        ]:
            if plot_path.exists():
                artifacts.append(
                    ArtifactReference(
                        artifact_type="svg_plot",
                        relative_path=self._relative(plot_path),
                        description=description,
                        producer="current_report_builder",
                    )
                )
        return artifacts
