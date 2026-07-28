from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class KnowledgeSource:
    source_key: str
    site_name: str
    topic: str
    url: str
    license_url: str


LICENSE_URLS: Dict[str, str] = {
    "niddk": "https://www.niddk.nih.gov/copyright",
    "cdc": "https://www.cdc.gov/other/agencymaterials.html",
    "medlineplus": "https://medlineplus.gov/about/using/usingcontent/",
}

LICENSE_SUMMARIES: Dict[str, str] = {
    "niddk": (
        "NIDDK majority copyright-free health information; text only; excludes logos, "
        "graphics, third-party material, and content carrying a separate copyright notice"
    ),
    "medlineplus": (
        "MedlinePlus health topic summaries are public domain; excludes licensed encyclopedia "
        "and drug content, images, illustrations, photos, and RSS material"
    ),
}


# Explicit allowlist: ingestion never follows content links recursively.
SOURCES: Tuple[KnowledgeSource, ...] = (
    KnowledgeSource("niddk", "NIDDK", "糖尿病基础", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "1型糖尿病", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-1-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "2型糖尿病", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "妊娠糖尿病", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "妊娠糖尿病定义", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/definition-facts", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "妊娠糖尿病症状与病因", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/symptoms-causes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "妊娠糖尿病检查与诊断", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/tests-diagnosis", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "妊娠糖尿病管理与治疗", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/management-treatment", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "预防妊娠糖尿病", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/prevention", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "糖尿病与妊娠", "https://www.niddk.nih.gov/health-information/diabetes/diabetes-pregnancy", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "单基因糖尿病", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/monogenic-neonatal-mellitus-mody", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "检查与诊断", "https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "血糖管理", "https://www.niddk.nih.gov/health-information/diabetes/overview/managing-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "糖尿病护理经济援助", "https://www.niddk.nih.gov/health-information/diabetes/financial-help-diabetes-care", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "健康生活", "https://www.niddk.nih.gov/health-information/diabetes/overview/healthy-living-with-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "人工胰腺", "https://www.niddk.nih.gov/health-information/diabetes/overview/managing-diabetes/artificial-pancreas", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "连续血糖监测", "https://www.niddk.nih.gov/health-information/diabetes/overview/managing-diabetes/continuous-glucose-monitoring", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "妊娠糖尿病产后管理", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/gestational/after-your-baby-is-born", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "胰岛素与药物", "https://www.niddk.nih.gov/health-information/diabetes/overview/insulin-medicines-treatments", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "预防并发症", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "低血糖", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/low-blood-glucose-hypoglycemia", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "足部护理", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/foot-problems", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "牙龈与口腔健康", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/gum-disease-dental-problems", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "眼部并发症", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-eye-disease", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "肾脏并发症", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/diabetic-kidney-disease", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "神经病变", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "自主神经病变", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies/autonomic-neuropathy", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "局灶性神经病变", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies/focal-neuropathies", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "周围神经病变", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies/peripheral-neuropathy", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "近端神经病变", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies/proximal-neuropathy", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "糖尿病神经病变基础", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/nerve-damage-diabetic-neuropathies/what-is-diabetic-neuropathy", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "性功能与膀胱问题", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/sexual-bladder-problems", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "心血管风险", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-problems/heart-disease-stroke", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "预防2型糖尿病", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-type-2-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "预防2型糖尿病行动计划", "https://www.niddk.nih.gov/health-information/diabetes/overview/preventing-type-2-diabetes/game-plan", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "2型糖尿病风险因素", "https://www.niddk.nih.gov/health-information/diabetes/overview/risk-factors-type-2-diabetes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "症状与病因", "https://www.niddk.nih.gov/health-information/diabetes/overview/symptoms-causes", LICENSE_URLS["niddk"]),
    KnowledgeSource("niddk", "NIDDK", "糖尿病前期与胰岛素抵抗", "https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/prediabetes-insulin-resistance", LICENSE_URLS["niddk"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病基础", "https://medlineplus.gov/diabetes.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "1型糖尿病", "https://medlineplus.gov/diabetestype1.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "2型糖尿病", "https://medlineplus.gov/diabetestype2.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病前期", "https://medlineplus.gov/prediabetes.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "妊娠糖尿病", "https://medlineplus.gov/diabetesandpregnancy.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "低血糖", "https://medlineplus.gov/hypoglycemia.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "高血糖", "https://medlineplus.gov/hyperglycemia.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病饮食", "https://medlineplus.gov/diabeticdiet.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病足", "https://medlineplus.gov/diabeticfoot.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病眼病", "https://medlineplus.gov/diabeticeyeproblems.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病肾病", "https://medlineplus.gov/diabetickidneyproblems.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病神经病变", "https://medlineplus.gov/diabeticnerveproblems.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "血糖", "https://medlineplus.gov/bloodglucose.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "A1C", "https://medlineplus.gov/a1c.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病性心脏病", "https://medlineplus.gov/diabeticheartdisease.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "碳水化合物代谢紊乱", "https://medlineplus.gov/carbohydratemetabolismdisorders.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "代谢综合征", "https://medlineplus.gov/metabolicsyndrome.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病药物", "https://medlineplus.gov/diabetesmedicines.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "预防糖尿病", "https://medlineplus.gov/howtopreventdiabetes.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "儿童与青少年糖尿病", "https://medlineplus.gov/diabetesinchildrenandteens.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "糖尿病并发症", "https://medlineplus.gov/diabetescomplications.html", LICENSE_URLS["medlineplus"]),
    KnowledgeSource("medlineplus", "MedlinePlus", "碳水化合物", "https://medlineplus.gov/carbohydrates.html", LICENSE_URLS["medlineplus"]),
)


def get_sources(source_key: str | None = None) -> Tuple[KnowledgeSource, ...]:
    if source_key is None:
        return SOURCES
    return tuple(source for source in SOURCES if source.source_key == source_key)
