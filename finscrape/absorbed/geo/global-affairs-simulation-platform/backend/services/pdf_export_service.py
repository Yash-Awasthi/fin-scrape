"""PDF报告导出 - 4类报告：快报/推演树/专题/复盘"""
import io
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.models.ir_event import AbstractIRGEvent
from backend.models.prediction import PredictionRun
from backend.models.scenario import ScenarioScript, ScenarioStep
from backend.models.outcome import ActualOutcome, PredictionEvaluation
from backend.models.theory_analysis import TheoryAnalysis, THEORY_DISPLAY_NAMES, THEORY_NAMES


def generate_pdf_report(
    db: Session,
    report_type: str,
    event_id: Optional[str] = None,
    run_id: Optional[str] = None,
) -> bytes:
    """生成PDF报告，type: event_brief/scenario_report/thematic_report/review_report"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os

        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/msyhbd.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
            "C:/Windows/Fonts/simkai.ttf",
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode MS.ttf",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        ]
        font_name = "Helvetica"
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CJK", fp))
                    font_name = "CJK"
                    break
                except Exception:
                    pass

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontName=font_name,
            fontSize=18,
            spaceAfter=12,
        )
        h1_style = ParagraphStyle("H1", parent=styles["Heading1"], fontName=font_name, fontSize=14, spaceAfter=8, spaceBefore=12)
        h2_style = ParagraphStyle("H2", parent=styles["Heading2"], fontName=font_name, fontSize=12, spaceAfter=6, spaceBefore=8)
        h3_style = ParagraphStyle("H3", parent=styles["Heading3"], fontName=font_name, fontSize=11, spaceAfter=4, spaceBefore=6)
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontName=font_name, fontSize=10, spaceAfter=4, leading=14)
        small_style = ParagraphStyle("Small", parent=styles["Normal"], fontName=font_name, fontSize=9, spaceAfter=3, textColor=colors.grey)

        story = []
        report_id = str(uuid.uuid4())[:8]
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        if report_type == "event_brief":
            story = _build_event_brief(db, event_id, run_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at)
        elif report_type == "scenario_report":
            story = _build_scenario_report(db, event_id, run_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at)
        elif report_type == "thematic_report":
            story = _build_thematic_report(db, event_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at)
        elif report_type == "review_report":
            story = _build_review_report(db, run_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at)
        else:
            story.append(Paragraph("未知报告类型", title_style))

        doc.build(story)
        buffer.seek(0)
        return buffer.read()

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PDF 生成服务不可用：ReportLab 未安装。请运行 pip install reportlab 后重试。",
        )


def _add_section(story, title, content_list, h2_style, body_style):
    """添加一个章节"""
    from reportlab.platypus import Paragraph, Spacer
    story.append(Paragraph(title, h2_style))
    if not content_list:
        story.append(Paragraph("暂无数据", body_style))
    else:
        for item in content_list:
            story.append(Paragraph(f"• {item}", body_style))
    story.append(Spacer(1, 6))


def _build_event_brief(db, event_id, run_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at):
    from reportlab.platypus import Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first() if event_id else None

    story.append(Paragraph("国际关系事件快报", title_style))
    story.append(Paragraph(f"报告ID: {report_id} | 生成时间: {generated_at}", small_style))
    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 12))

    if not event:
        story.append(Paragraph("未找到指定事件数据", body_style))
        return story

    story.append(Paragraph("一、事件基本信息", h1_style))
    
    basic_info = [
        ["事件标题", event.event_title or "未知"],
        ["事件类型", event.event_type or "未分类"],
        ["危机阶段", event.stage_of_crisis or "未知"],
        ["所在地区", event.region or "未知"],
        ["置信度", f"{int((event.event_confidence or 0) * 100)}%"],
    ]
    
    basic_table = Table(basic_info, colWidths=[3*cm, 12*cm])
    basic_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(basic_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("二、关键行为主体", h1_style))
    actors = event.key_actors or []
    roles = event.actor_roles or {}
    if actors:
        actor_data = [["行为主体", "角色定位"]]
        for actor in actors:
            role = roles.get(actor, "未定义")
            actor_data.append([actor, role])
        actor_table = Table(actor_data, colWidths=[5*cm, 10*cm])
        actor_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.5)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(actor_table)
    else:
        story.append(Paragraph("暂无行为主体数据", body_style))
    story.append(Spacer(1, 8))

    if event.key_locations:
        story.append(Paragraph("关键地点", h2_style))
        story.append(Paragraph("、 ".join(event.key_locations), body_style))
        story.append(Spacer(1, 6))

    if event.strategic_dimensions:
        story.append(Paragraph("战略维度", h2_style))
        story.append(Paragraph("、 ".join(event.strategic_dimensions), body_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph("三、当前危机阶段分析", h1_style))
    story.append(Paragraph("当前力量对比", h2_style))
    story.append(Paragraph(event.current_balance or "暂无评估", body_style))
    story.append(Spacer(1, 6))

    _add_section(story, "主要驱动力", event.driving_forces, h2_style, body_style)
    _add_section(story, "即时触发器", event.immediate_triggers, h2_style, body_style)
    _add_section(story, "主要约束条件", event.constraints, h2_style, body_style)

    story.append(Paragraph("四、主要风险点", h1_style))
    risks = event.major_risks or []
    if risks:
        for i, r in enumerate(risks, 1):
            story.append(Paragraph(f"{i}. {r}", body_style))
    else:
        story.append(Paragraph("暂无风险数据", body_style))
    story.append(Spacer(1, 6))

    if event.current_opportunities:
        story.append(Paragraph("当前机会窗口", h2_style))
        for o in event.current_opportunities:
            story.append(Paragraph(f"• {o}", body_style))
        story.append(Spacer(1, 6))

    story.append(Paragraph("五、短期走向研判", h1_style))
    
    scripts = db.query(ScenarioScript).filter_by(event_id=event_id).all()
    if scripts:
        direction_map = {"escalation": "升级方向", "stalemate": "僵持方向", "de_escalation": "缓和方向"}
        for direction in ["escalation", "stalemate", "de_escalation"]:
            dir_scripts = [s for s in scripts if s.direction_type == direction]
            if not dir_scripts:
                continue
            
            total_prob = sum(s.probability_central or 0 for s in dir_scripts) / len(dir_scripts) if dir_scripts else 0
            story.append(Paragraph(
                f"{direction_map.get(direction, direction)}（综合概率 {int(total_prob * 100)}%）",
                h2_style
            ))
            
            for script in dir_scripts[:3]:
                prob_low = int((script.probability_low or 0) * 100)
                prob_high = int((script.probability_high or 0) * 100)
                prob_c = int((script.probability_central or 0) * 100)
                story.append(Paragraph(
                    f"• {script.script_title}（{prob_low}%–{prob_high}%，中心 {prob_c}%）",
                    body_style
                ))
                if script.script_description:
                    desc = script.script_description[:200] + "..." if len(script.script_description or "") > 200 else script.script_description
                    story.append(Paragraph(f"  {desc}", small_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("暂无推演剧本数据，无法进行短期走向研判", body_style))

    if run_id:
        story.append(HRFlowable(width="100%", color=colors.grey))
        story.append(Spacer(1, 8))
        story.append(Paragraph("附录：关联推演详情", h1_style))
        story.append(Paragraph(f"推演 Run ID: {run_id}", small_style))
        
        run = db.query(PredictionRun).filter_by(run_id=run_id).first()
        if run and run.summary:
            story.append(Paragraph("推演摘要", h2_style))
            story.append(Paragraph(run.summary, body_style))

    return story


def _build_scenario_report(db, event_id, run_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at):
    from reportlab.platypus import Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first() if event_id else None
    
    if run_id:
        scripts = db.query(ScenarioScript).filter_by(event_id=event_id, run_id=run_id).all()
    else:
        scripts = db.query(ScenarioScript).filter_by(event_id=event_id).all()

    story.append(Paragraph("情景推演报告", title_style))
    story.append(Paragraph(f"报告ID: {report_id} | Run ID: {run_id or 'N/A'} | {generated_at}", small_style))
    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 12))

    if event:
        story.append(Paragraph("一、推演基本信息", h1_style))
        
        event_info = [
            ["事件标题", event.event_title or "未知"],
            ["事件类型", event.event_type or "未分类"],
            ["危机阶段", event.stage_of_crisis or "未知"],
            ["所在地区", event.region or "未知"],
            ["剧本总数", str(len(scripts))],
        ]
        
        event_table = Table(event_info, colWidths=[3*cm, 12*cm])
        event_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(event_table)
        story.append(Spacer(1, 10))

        if event.key_actors:
            story.append(Paragraph("关键行为主体", h2_style))
            story.append(Paragraph("、 ".join(event.key_actors), body_style))
            story.append(Spacer(1, 6))

    direction_map = {"escalation": "升级方向剧本", "stalemate": "僵持方向剧本", "de_escalation": "缓和方向剧本"}
    section_num = 2

    for direction in ["escalation", "stalemate", "de_escalation"]:
        dir_scripts = [s for s in scripts if s.direction_type == direction]
        if not dir_scripts:
            continue

        story.append(Paragraph(f"{section_num}、{direction_map.get(direction, direction)}", h1_style))
        section_num += 1

        total_prob = sum(s.probability_central or 0 for s in dir_scripts) / len(dir_scripts) if dir_scripts else 0
        story.append(Paragraph(f"该方向综合概率：{int(total_prob * 100)}%，共 {len(dir_scripts)} 个剧本", body_style))
        story.append(Spacer(1, 8))

        for idx, script in enumerate(dir_scripts, 1):
            story.append(Paragraph(f"剧本 {idx}：{script.script_title}", h2_style))
            
            prob_low = int((script.probability_low or 0) * 100)
            prob_high = int((script.probability_high or 0) * 100)
            prob_c = int((script.probability_central or 0) * 100)
            
            prob_info = [
                ["概率区间", f"{prob_low}% – {prob_high}%"],
                ["中心估计", f"{prob_c}%"],
                ["置信度", script.confidence_level or "未评估"],
            ]
            prob_table = Table(prob_info, colWidths=[3*cm, 5*cm])
            prob_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.98)),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(prob_table)
            story.append(Spacer(1, 4))

            if script.script_description:
                story.append(Paragraph("剧本描述", h3_style))
                story.append(Paragraph(script.script_description, body_style))

            if script.why_this_script_is_realistic:
                story.append(Paragraph("可信性分析", h3_style))
                story.append(Paragraph(script.why_this_script_is_realistic, body_style))

            if script.trigger_conditions:
                story.append(Paragraph("触发条件", h3_style))
                for tc in script.trigger_conditions:
                    story.append(Paragraph(f"• {tc}", body_style))

            if script.invalidation_conditions:
                story.append(Paragraph("失效条件", h3_style))
                for ic in script.invalidation_conditions:
                    story.append(Paragraph(f"• {ic}", body_style))

            if script.supporting_factors:
                story.append(Paragraph("支持因素", h3_style))
                for sf in script.supporting_factors:
                    story.append(Paragraph(f"✓ {sf}", body_style))

            if script.opposing_factors:
                story.append(Paragraph("反对因素", h3_style))
                for of in script.opposing_factors:
                    story.append(Paragraph(f"✗ {of}", body_style))

            if script.uncertainty_notes:
                story.append(Paragraph("不确定性说明", h3_style))
                story.append(Paragraph(script.uncertainty_notes, small_style))

            steps = db.query(ScenarioStep).filter_by(script_id=script.script_id).order_by(ScenarioStep.step_number).all()
            if steps:
                story.append(Paragraph("推演步骤链", h3_style))
                for step in steps:
                    story.append(Paragraph(f"步骤 {step.step_number}：{step.title}", body_style))
                    
                    if step.which_actor_acts_first:
                        story.append(Paragraph(f"  行动方：{step.which_actor_acts_first}", small_style))
                    if step.why_this_step_happens:
                        story.append(Paragraph(f"  发生原因：{step.why_this_step_happens}", small_style))
                    
                    if step.how_other_actors_react:
                        story.append(Paragraph("  各方反应：", small_style))
                        for actor, reaction in step.how_other_actors_react.items():
                            story.append(Paragraph(f"    - {actor}：{reaction}", small_style))
                    
                    if step.key_drivers:
                        story.append(Paragraph(f"  驱动因素：{', '.join(str(d) for d in step.key_drivers[:3])}", small_style))
                    if step.constraints:
                        story.append(Paragraph(f"  约束条件：{', '.join(str(c) for c in step.constraints[:3])}", small_style))
                    if step.supporting_evidence:
                        story.append(Paragraph(f"  支持证据：{', '.join(str(e) for e in step.supporting_evidence[:2])}", small_style))
                    if step.uncertainty:
                        story.append(Paragraph(f"  不确定性：{step.uncertainty}", small_style))
                    
                    story.append(Spacer(1, 4))

            story.append(Spacer(1, 8))
            story.append(HRFlowable(width="80%", color=colors.lightgrey))
            story.append(Spacer(1, 6))

    return story


def _build_thematic_report(db, event_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at):
    from reportlab.platypus import Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    event = db.query(AbstractIRGEvent).filter_by(event_id=event_id).first() if event_id else None
    analyses = db.query(TheoryAnalysis).filter_by(event_id=event_id).all() if event_id else []
    analyses_dict = {a.theory_name: a for a in analyses}

    story.append(Paragraph("专题分析报告", title_style))
    story.append(Paragraph(f"报告ID: {report_id} | {generated_at}", small_style))
    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 12))

    if event:
        story.append(Paragraph("一、事件背景", h1_style))
        
        event_info = [
            ["事件标题", event.event_title or "未知"],
            ["事件类型", event.event_type or "未分类"],
            ["危机阶段", event.stage_of_crisis or "未知"],
            ["所在地区", event.region or "未知"],
        ]
        
        event_table = Table(event_info, colWidths=[3*cm, 12*cm])
        event_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(event_table)
        story.append(Spacer(1, 6))

        if event.key_actors:
            story.append(Paragraph("关键行为主体", h2_style))
            story.append(Paragraph("、 ".join(event.key_actors), body_style))
        story.append(Spacer(1, 8))

    section_num = 2
    for theory_name in THEORY_NAMES:
        display_name = THEORY_DISPLAY_NAMES.get(theory_name, theory_name)
        story.append(Paragraph(f"{section_num}、{display_name}视角", h1_style))
        section_num += 1

        analysis = analyses_dict.get(theory_name)
        if not analysis:
            story.append(Paragraph("该理论视角暂无分析数据", body_style))
            story.append(Spacer(1, 8))
            continue

        if analysis.core_assumption:
            story.append(Paragraph("核心假设", h2_style))
            story.append(Paragraph(analysis.core_assumption, body_style))

        if analysis.interpretation:
            story.append(Paragraph("事件解读", h2_style))
            story.append(Paragraph(analysis.interpretation, body_style))

        if analysis.main_drivers:
            story.append(Paragraph("主要驱动力", h2_style))
            for driver in analysis.main_drivers:
                story.append(Paragraph(f"• {driver}", body_style))

        if analysis.likely_actor_responses:
            story.append(Paragraph("预期行为反应", h2_style))
            for actor, response in analysis.likely_actor_responses.items():
                story.append(Paragraph(f"• {actor}：{response}", body_style))

        if analysis.escalation_implications:
            story.append(Paragraph("升级含义", h2_style))
            for impl in analysis.escalation_implications:
                story.append(Paragraph(f"• {impl}", body_style))

        if analysis.deescalation_implications:
            story.append(Paragraph("缓和含义", h2_style))
            for impl in analysis.deescalation_implications:
                story.append(Paragraph(f"• {impl}", body_style))

        if analysis.weaknesses:
            story.append(Paragraph("理论局限性", h2_style))
            for weakness in analysis.weaknesses:
                story.append(Paragraph(f"• {weakness}", body_style))

        if analysis.counterarguments:
            story.append(Paragraph("反驳论点", h2_style))
            for arg in analysis.counterarguments:
                story.append(Paragraph(f"• {arg}", body_style))

        if analysis.confidence_note:
            story.append(Paragraph("置信度说明", h2_style))
            story.append(Paragraph(analysis.confidence_note, small_style))

        story.append(Spacer(1, 8))

    story.append(Paragraph(f"{section_num}、综合研判", h1_style))
    
    if analyses:
        story.append(Paragraph("各理论视角对比", h2_style))
        
        comparison_data = [["理论视角", "核心观点摘要"]]
        for theory_name in THEORY_NAMES:
            analysis = analyses_dict.get(theory_name)
            display_name = THEORY_DISPLAY_NAMES.get(theory_name, theory_name)
            summary = ""
            if analysis and analysis.interpretation:
                summary = analysis.interpretation[:100] + "..." if len(analysis.interpretation) > 100 else analysis.interpretation
            comparison_data.append([display_name, summary or "暂无分析"])
        
        comparison_table = Table(comparison_data, colWidths=[4*cm, 11*cm])
        comparison_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.Color(0.2, 0.3, 0.5)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        story.append(comparison_table)
    else:
        story.append(Paragraph("暂无理论分析数据，请先运行分析生成理论视角解读", body_style))

    return story


def _build_review_report(db, run_id, story, title_style, h1_style, h2_style, h3_style, body_style, small_style, report_id, generated_at):
    from reportlab.platypus import Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    run = db.query(PredictionRun).filter_by(run_id=run_id).first() if run_id else None
    outcome = db.query(ActualOutcome).filter_by(related_run_id=run_id).first() if run_id else None
    evaluation = db.query(PredictionEvaluation).filter_by(run_id=run_id).first() if run_id else None

    story.append(Paragraph("预测复盘报告", title_style))
    story.append(Paragraph(f"报告ID: {report_id} | Run ID: {run_id or 'N/A'} | {generated_at}", small_style))
    story.append(HRFlowable(width="100%", color=colors.grey))
    story.append(Spacer(1, 12))

    if not run:
        story.append(Paragraph("未找到指定推演数据", body_style))
        return story

    story.append(Paragraph("一、推演执行摘要", h1_style))
    
    run_info = [
        ["Run ID", run.run_id or "未知"],
        ["事件 ID", run.event_id or "未知"],
        ["创建时间", run.created_at.strftime("%Y-%m-%d %H:%M") if run.created_at else "未知"],
        ["状态", run.status or "未知"],
    ]
    
    run_table = Table(run_info, colWidths=[3*cm, 12*cm])
    run_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(run_table)
    story.append(Spacer(1, 6))

    if run.summary:
        story.append(Paragraph("推演摘要", h2_style))
        story.append(Paragraph(run.summary, body_style))

    if run.script_ids:
        story.append(Paragraph("预测剧本列表", h2_style))
        scripts = db.query(ScenarioScript).filter(ScenarioScript.script_id.in_(run.script_ids)).all()
        for script in scripts:
            prob_c = int((script.probability_central or 0) * 100)
            story.append(Paragraph(f"• [{script.direction_type}] {script.script_title}（{prob_c}%）", body_style))

    story.append(Paragraph("二、实际发生情况", h1_style))
    if outcome:
        outcome_info = [
            ["实际事件类型", outcome.actual_event_type or "未记录"],
            ["记录时间", outcome.recorded_at.strftime("%Y-%m-%d %H:%M") if outcome.recorded_at else "未知"],
        ]
        outcome_table = Table(outcome_info, colWidths=[3*cm, 12*cm])
        outcome_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(outcome_table)
        story.append(Spacer(1, 6))

        if outcome.actual_summary:
            story.append(Paragraph("实际结果描述", h2_style))
            story.append(Paragraph(outcome.actual_summary, body_style))

        if outcome.matched_script_id:
            story.append(Paragraph("命中剧本分析", h2_style))
            matched_script = db.query(ScenarioScript).filter_by(script_id=outcome.matched_script_id).first()
            if matched_script:
                story.append(Paragraph(f"命中剧本：{matched_script.script_title}", body_style))
                story.append(Paragraph(f"方向类型：{matched_script.direction_type}", body_style))
                if matched_script.script_description:
                    story.append(Paragraph(f"剧本描述：{matched_script.script_description}", body_style))
    else:
        story.append(Paragraph("暂无实际结果记录", body_style))

    story.append(Paragraph("三、偏差识别", h1_style))
    if evaluation:
        eval_info = [
            ["剧本命中", "是" if evaluation.script_hit else "否"],
            ["步骤命中率", f"{int((evaluation.node_hit_rate or 0) * 100)}%" if evaluation.node_hit_rate else "未评估"],
            ["主要错误类型", evaluation.main_error_category or "未分类"],
        ]
        eval_table = Table(eval_info, colWidths=[3*cm, 12*cm])
        eval_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'CJK'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.9, 0.9, 0.95)),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(eval_table)
        story.append(Spacer(1, 6))

        if evaluation.detailed_error_analysis:
            story.append(Paragraph("误差原因分析", h2_style))
            story.append(Paragraph(evaluation.detailed_error_analysis, body_style))

        if evaluation.correct_aspects:
            story.append(Paragraph("预测正确的方面", h2_style))
            for aspect in evaluation.correct_aspects:
                story.append(Paragraph(f"✓ {aspect}", body_style))

        if evaluation.incorrect_aspects:
            story.append(Paragraph("预测错误的方面", h2_style))
            for aspect in evaluation.incorrect_aspects:
                story.append(Paragraph(f"✗ {aspect}", body_style))
    else:
        story.append(Paragraph("暂无评估数据", body_style))

    story.append(Paragraph("四、改进建议", h1_style))
    if evaluation and evaluation.suggested_adjustments:
        for i, suggestion in enumerate(evaluation.suggested_adjustments, 1):
            story.append(Paragraph(f"{i}. {suggestion}", body_style))
    else:
        story.append(Paragraph("暂无改进建议", body_style))

    story.append(Paragraph("五、经验总结", h1_style))
    if evaluation:
        story.append(Paragraph("本次预测复盘的核心经验：", body_style))
        
        if evaluation.script_hit:
            story.append(Paragraph("• 预测方向正确，剧本命中", body_style))
        else:
            story.append(Paragraph("• 预测方向存在偏差，需改进", body_style))
        
        if evaluation.node_hit_rate and evaluation.node_hit_rate > 0.6:
            story.append(Paragraph(f"• 步骤预测准确率较高（{int(evaluation.node_hit_rate * 100)}%）", body_style))
        elif evaluation.node_hit_rate:
            story.append(Paragraph(f"• 步骤预测准确率有待提升（{int(evaluation.node_hit_rate * 100)}%）", body_style))
        
        if evaluation.main_error_category:
            error_map = {
                "evidence_miss": "证据遗漏",
                "actor_profile_error": "行为主体画像错误",
                "historical_analogy_failure": "历史类比失效",
                "timing_error": "时机判断错误",
                "template_overfitting": "模板过拟合",
                "black_swan": "黑天鹅事件",
            }
            story.append(Paragraph(f"• 主要误差来源：{error_map.get(evaluation.main_error_category, evaluation.main_error_category)}", body_style))
    else:
        story.append(Paragraph("请先完成预测评估以生成经验总结", body_style))

    return story

