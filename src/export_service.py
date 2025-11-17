"""
Data Export Service for Korean Mental Health Counseling System
Provides CSV and PDF export functionality for conversation history and reports
"""

import os
import io
import csv
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy imports for heavy libraries
_reportlab_available = False
_pandas_available = False


def check_reportlab():
    """Check if reportlab is available"""
    global _reportlab_available
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        _reportlab_available = True
    except ImportError:
        _reportlab_available = False
    return _reportlab_available


def check_pandas():
    """Check if pandas is available"""
    global _pandas_available
    try:
        import pandas as pd
        _pandas_available = True
    except ImportError:
        _pandas_available = False
    return _pandas_available


class ExportService:
    """
    Service for exporting conversation data and generating reports

    Supported formats:
    - CSV: Conversation history, user statistics
    - PDF: Session reports, assessment summaries
    - JSON: Raw data export
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.export_dir = Path(self.config.get("export_dir", "data/exports"))
        self.export_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            "csv_exports": 0,
            "pdf_exports": 0,
            "json_exports": 0,
            "errors": 0
        }

        logger.info("ExportService initialized")

    def export_conversation_to_csv(
        self,
        conversation_history: List[Dict[str, Any]],
        session_id: str,
        include_metadata: bool = True
    ) -> bytes:
        """
        Export conversation history to CSV format

        Args:
            conversation_history: List of message dictionaries
            session_id: Session identifier
            include_metadata: Include timestamps and other metadata

        Returns:
            CSV data as bytes
        """
        self.stats["csv_exports"] += 1

        try:
            output = io.StringIO()

            # Define CSV headers
            if include_metadata:
                headers = ["timestamp", "role", "message", "emotion", "risk_level"]
            else:
                headers = ["role", "message"]

            writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
            writer.writeheader()

            for msg in conversation_history:
                row = {
                    "role": msg.get("role", "unknown"),
                    "message": msg.get("content", msg.get("message", ""))
                }

                if include_metadata:
                    row["timestamp"] = msg.get("time", msg.get("timestamp", ""))
                    row["emotion"] = msg.get("emotion", "")
                    row["risk_level"] = msg.get("risk_level", "")

                writer.writerow(row)

            csv_data = output.getvalue().encode('utf-8-sig')  # BOM for Korean Excel compatibility

            logger.info(f"Exported {len(conversation_history)} messages to CSV for session {session_id}")
            return csv_data

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"CSV export error: {e}")
            raise

    def export_user_stats_to_csv(
        self,
        user_id: str,
        stats_data: Dict[str, Any]
    ) -> bytes:
        """
        Export user statistics to CSV

        Args:
            user_id: User identifier
            stats_data: User statistics dictionary

        Returns:
            CSV data as bytes
        """
        self.stats["csv_exports"] += 1

        try:
            output = io.StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow(["User Statistics Report"])
            writer.writerow(["User ID", user_id])
            writer.writerow(["Export Date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow([])

            # Statistics
            writer.writerow(["Metric", "Value"])

            for key, value in stats_data.items():
                if isinstance(value, dict):
                    writer.writerow([key, ""])
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"  {sub_key}", sub_value])
                elif isinstance(value, list):
                    writer.writerow([key, ", ".join(map(str, value))])
                else:
                    writer.writerow([key, value])

            csv_data = output.getvalue().encode('utf-8-sig')

            logger.info(f"Exported user stats to CSV for user {user_id}")
            return csv_data

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"User stats CSV export error: {e}")
            raise

    def export_assessment_results_to_csv(
        self,
        assessment_results: List[Dict[str, Any]]
    ) -> bytes:
        """
        Export assessment results to CSV

        Args:
            assessment_results: List of assessment result dictionaries

        Returns:
            CSV data as bytes
        """
        self.stats["csv_exports"] += 1

        try:
            output = io.StringIO()

            headers = ["date", "assessment_type", "score", "severity", "recommendations"]
            writer = csv.DictWriter(output, fieldnames=headers)
            writer.writeheader()

            for result in assessment_results:
                row = {
                    "date": result.get("date", ""),
                    "assessment_type": result.get("type", ""),
                    "score": result.get("score", ""),
                    "severity": result.get("severity", ""),
                    "recommendations": "; ".join(result.get("recommendations", []))
                }
                writer.writerow(row)

            csv_data = output.getvalue().encode('utf-8-sig')

            logger.info(f"Exported {len(assessment_results)} assessment results to CSV")
            return csv_data

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Assessment CSV export error: {e}")
            raise

    def generate_session_report_pdf(
        self,
        session_data: Dict[str, Any],
        conversation_history: List[Dict[str, Any]],
        emotion_analysis: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Generate PDF report for a counseling session

        Args:
            session_data: Session metadata
            conversation_history: List of messages
            emotion_analysis: Optional emotion analysis summary

        Returns:
            PDF data as bytes
        """
        self.stats["pdf_exports"] += 1

        if not check_reportlab():
            raise ImportError("reportlab is not installed. Run: pip install reportlab")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)

            # Build PDF content
            story = []
            styles = getSampleStyleSheet()

            # Title
            story.append(Paragraph("상담 세션 보고서", styles['Title']))
            story.append(Paragraph("Mental Health Counseling Session Report", styles['Heading2']))
            story.append(Spacer(1, 0.5*cm))

            # Session Info
            session_info = [
                ["세션 ID", session_data.get("session_id", "N/A")],
                ["날짜", session_data.get("date", datetime.now().strftime("%Y-%m-%d"))],
                ["시간", session_data.get("time", datetime.now().strftime("%H:%M"))],
                ["상담사", session_data.get("counselor_name", "AI 상담사")],
                ["상담 유형", session_data.get("counselor_type", "일반 상담")],
                ["총 메시지 수", str(len(conversation_history))],
            ]

            table = Table(session_info, colWidths=[4*cm, 10*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.5*cm))

            # Emotion Summary (if provided)
            if emotion_analysis:
                story.append(Paragraph("감정 분석 요약", styles['Heading3']))
                emotion_data = [
                    ["주요 감정", emotion_analysis.get("primary_emotion", "N/A")],
                    ["감정 강도", str(emotion_analysis.get("intensity", "N/A"))],
                    ["위험 수준", emotion_analysis.get("risk_level", "LOW")],
                ]

                emotion_table = Table(emotion_data, colWidths=[4*cm, 10*cm])
                emotion_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(emotion_table)
                story.append(Spacer(1, 0.5*cm))

            # Conversation Summary
            story.append(Paragraph("대화 내용 요약", styles['Heading3']))
            story.append(Spacer(1, 0.2*cm))

            # Show first and last few messages
            max_messages = min(10, len(conversation_history))
            messages_to_show = conversation_history[:max_messages]

            for msg in messages_to_show:
                role = "사용자" if msg.get("role") == "user" else "상담사"
                content = msg.get("content", msg.get("message", ""))[:200]
                if len(msg.get("content", msg.get("message", ""))) > 200:
                    content += "..."

                story.append(Paragraph(f"<b>{role}:</b> {content}", styles['Normal']))
                story.append(Spacer(1, 0.2*cm))

            if len(conversation_history) > max_messages:
                story.append(Paragraph(f"... ({len(conversation_history) - max_messages}개 메시지 생략)", styles['Italic']))

            # Footer
            story.append(Spacer(1, 1*cm))
            story.append(Paragraph(
                "이 보고서는 마음챗 AI 상담 시스템에서 자동 생성되었습니다.",
                styles['Italic']
            ))
            story.append(Paragraph(
                f"생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                styles['Italic']
            ))

            # Build PDF
            doc.build(story)

            pdf_data = buffer.getvalue()
            buffer.close()

            logger.info(f"Generated PDF report for session {session_data.get('session_id', 'unknown')}")
            return pdf_data

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"PDF generation error: {e}")
            raise

    def generate_assessment_report_pdf(
        self,
        user_id: str,
        assessment_type: str,
        score: int,
        severity: str,
        responses: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> bytes:
        """
        Generate PDF report for psychological assessment

        Args:
            user_id: User identifier
            assessment_type: Type of assessment (PHQ-9, GAD-7, K-10)
            score: Total score
            severity: Severity level
            responses: Individual question responses
            recommendations: List of recommendations

        Returns:
            PDF data as bytes
        """
        self.stats["pdf_exports"] += 1

        if not check_reportlab():
            raise ImportError("reportlab is not installed")

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors

            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()

            # Title
            story.append(Paragraph(f"{assessment_type} 심리 평가 보고서", styles['Title']))
            story.append(Spacer(1, 0.5*cm))

            # Basic Info
            info_data = [
                ["평가 유형", assessment_type],
                ["평가 날짜", datetime.now().strftime("%Y-%m-%d")],
                ["총점", f"{score}점"],
                ["심각도", severity],
            ]

            info_table = Table(info_data, colWidths=[4*cm, 10*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 0.5*cm))

            # Score Interpretation
            story.append(Paragraph("점수 해석", styles['Heading3']))
            interpretation = self._get_assessment_interpretation(assessment_type, score)
            story.append(Paragraph(interpretation, styles['Normal']))
            story.append(Spacer(1, 0.5*cm))

            # Recommendations
            if recommendations:
                story.append(Paragraph("권고사항", styles['Heading3']))
                for i, rec in enumerate(recommendations, 1):
                    story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                    story.append(Spacer(1, 0.1*cm))

            story.append(Spacer(1, 1*cm))

            # Disclaimer
            story.append(Paragraph(
                "주의: 이 평가는 참고용이며, 전문적인 진단을 대체하지 않습니다. "
                "심각한 증상이 있는 경우 정신건강 전문가와 상담하시기 바랍니다.",
                styles['Italic']
            ))

            # Build PDF
            doc.build(story)

            pdf_data = buffer.getvalue()
            buffer.close()

            logger.info(f"Generated {assessment_type} assessment PDF for user")
            return pdf_data

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Assessment PDF generation error: {e}")
            raise

    def _get_assessment_interpretation(self, assessment_type: str, score: int) -> str:
        """Get interpretation text for assessment score"""

        if assessment_type == "PHQ-9":
            if score <= 4:
                return "최소한의 우울 증상 (Minimal depression). 현재 큰 문제가 없습니다."
            elif score <= 9:
                return "경도 우울 증상 (Mild depression). 자기 관리와 모니터링을 권장합니다."
            elif score <= 14:
                return "중등도 우울 증상 (Moderate depression). 전문가 상담을 고려하시기 바랍니다."
            elif score <= 19:
                return "중등도-중증 우울 증상 (Moderately severe). 전문가 치료가 권장됩니다."
            else:
                return "중증 우울 증상 (Severe depression). 즉각적인 전문가 개입이 필요합니다."

        elif assessment_type == "GAD-7":
            if score <= 4:
                return "최소한의 불안 증상 (Minimal anxiety)."
            elif score <= 9:
                return "경도 불안 증상 (Mild anxiety)."
            elif score <= 14:
                return "중등도 불안 증상 (Moderate anxiety). 전문가 상담을 권장합니다."
            else:
                return "중증 불안 증상 (Severe anxiety). 전문가 치료가 필요합니다."

        elif assessment_type == "K-10":
            if score <= 15:
                return "낮은 심리적 고통 수준 (Low psychological distress)."
            elif score <= 21:
                return "중간 심리적 고통 수준 (Moderate psychological distress)."
            elif score <= 29:
                return "높은 심리적 고통 수준 (High psychological distress)."
            else:
                return "매우 높은 심리적 고통 수준 (Very high psychological distress)."

        return "평가 결과를 해석할 수 없습니다."

    def export_to_json(self, data: Any, pretty: bool = True) -> bytes:
        """
        Export data to JSON format

        Args:
            data: Data to export (dict, list, etc.)
            pretty: Format with indentation

        Returns:
            JSON data as bytes
        """
        self.stats["json_exports"] += 1

        try:
            if pretty:
                json_str = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            else:
                json_str = json.dumps(data, ensure_ascii=False, default=str)

            return json_str.encode('utf-8')

        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"JSON export error: {e}")
            raise

    def get_stats(self) -> Dict[str, Any]:
        """Get export service statistics"""
        return {
            **self.stats,
            "timestamp": datetime.utcnow().isoformat()
        }


# Singleton instance
_export_service = None


def get_export_service() -> ExportService:
    """Get singleton export service instance"""
    global _export_service
    if _export_service is None:
        _export_service = ExportService()
    return _export_service
