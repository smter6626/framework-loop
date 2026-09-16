"""F4 default Chinese governance prompt template tests."""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATIC_TEMPLATE = ROOT / "templates" / "static_prompt_zh.md"
RUNTIME_TEMPLATE = ROOT / "templates" / "runtime_prompt_zh.md"
README_EN = ROOT / "README.md"
README_ZH = ROOT / "README.zh-CN.md"

STATIC_SOURCE = (
    "/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/"
    "structured-llm-execution-framework_static.md"
)
RUNTIME_SOURCE = (
    "/Users/smterpro/Workspace/Tools/structured-llm-execution-framework/"
    "structured-llm-execution-framework_runtime.md"
)
STATIC_SOURCE_SHA256 = (
    "e3ff93b4136c0d3d87d7f1a319ca9c4513f831327daf18aea46f9f3d6659daf7"
)
RUNTIME_SOURCE_SHA256 = (
    "3cbc4c93adff6ac2b1fb351a8a81f4b65dbd73b4de28ee2d0d4141522258ab54"
)


class PromptTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.static = STATIC_TEMPLATE.read_text(encoding="utf-8")
        cls.runtime = RUNTIME_TEMPLATE.read_text(encoding="utf-8")

    def test_templates_exist_are_utf8_and_default_to_chinese(self):
        for path, text in (
            (STATIC_TEMPLATE, self.static),
            (RUNTIME_TEMPLATE, self.runtime),
        ):
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file())
                path.read_bytes().decode("utf-8", errors="strict")
                chinese_characters = len(re.findall(r"[\u4e00-\u9fff]", text))
                self.assertGreater(chinese_characters, 300)

    def test_provenance_headers_are_exact_and_define_maintenance_boundary(self):
        for text, source, source_hash in (
            (self.static, STATIC_SOURCE, STATIC_SOURCE_SHA256),
            (self.runtime, RUNTIME_SOURCE, RUNTIME_SOURCE_SHA256),
        ):
            with self.subTest(source=source):
                header = "\n".join(text.splitlines()[:10])
                self.assertIn(f"`{source}`", header)
                self.assertIn(f"`{source_hash}`", header)
                self.assertIn("来源版本：Framework v1.2", header)
                self.assertIn("外部来源只读", header)
                self.assertIn("不会自动同步", header)
                self.assertIn("重新核对来源路径与 SHA-256", header)
                self.assertIn("接受独立审核", header)

    def test_each_template_contains_a_directly_copyable_prompt(self):
        for text in (self.static, self.runtime):
            with self.subTest(title=text.splitlines()[0]):
                marker = "## 可复制 Prompt"
                self.assertIn(marker, text)
                prompt = text.split(marker, 1)[1].strip()
                self.assertGreater(len(prompt), 2000)
                self.assertTrue(prompt.startswith("你是当前任务"))

    def test_static_and_runtime_responsibilities_are_separated(self):
        self.assertIn("Static 只写稳定合同", self.static)
        self.assertIn("不要写当前 Active Step", self.static)
        self.assertIn("当前执行状态必须留在独立的 Runtime 中", self.static)
        self.assertIn("恢复并维护一份当前权威的 Runtime 状态", self.runtime)
        self.assertIn("Runtime 不得修改、取消或扩大 Static", self.runtime)
        self.assertIn("Executor 默认不得修改 Static / Runtime", self.runtime)

    def test_shared_governance_invariants_and_privacy_boundary_are_present(self):
        combined = self.static + self.runtime
        required = (
            "Human Owner",
            "Human Decision Gate",
            "Task-local freeze",
            "Supersession Persistence",
            "Evidence and Privacy Boundary",
        )
        for invariant in required:
            with self.subTest(invariant=invariant):
                self.assertIn(invariant, combined)
        self.assertIn("不得把 self-check 当作最终验收", self.runtime)
        self.assertIn("Executor report 只能帮助定位，不能替代 evidence", self.runtime)
        self.assertIn("凭证", combined)
        self.assertIn("秘密", combined)
        self.assertIn("个人信息", combined)
        self.assertNotRegex(combined, r"(?:Bearer\s+|sk-)[A-Za-z0-9_-]{12,}")

    def test_runtime_contains_single_step_independent_review_and_transitions(self):
        self.assertIn("Single Active Step", self.runtime)
        self.assertIn("Evidence-Backed Transition", self.runtime)
        independent_conditions = (
            "独立 evidence access",
            "独立 verdict formation",
            "独立 evidence-sufficiency judgment",
        )
        for condition in independent_conditions:
            with self.subTest(condition=condition):
                self.assertIn(condition, self.runtime)
        self.assertIn("Executor self-report", self.runtime)
        self.assertIn("最终 acceptance", self.runtime)

    def test_runtime_contains_complete_pending_deadline_contract(self):
        self.assertIn("max(n - k - 1, 0)", self.runtime)
        self.assertIn("在激活下一顶层 Step 前执行 deadline gate", self.runtime)
        statuses = (
            "OPEN_NON_BLOCKING",
            "DUE_NEXT",
            "BLOCKING",
            "PERMANENTLY_NON_BLOCKING",
            "RESOLVED",
            "SUPERSEDED",
        )
        for status in statuses:
            with self.subTest(status=status):
                self.assertIn(f"`{status}`", self.runtime)

    def test_templates_are_tailorable_and_unknowns_remain_explicit(self):
        for text in (self.static, self.runtime):
            with self.subTest(title=text.splitlines()[0]):
                self.assertIn("推荐输入结构", text)
                self.assertRegex(text, r"不是(?:每个|要求所有)任务")
                self.assertIn("低风险", text)
        self.assertIn("TO_CONFIRM", self.static)
        self.assertIn("REQUIRES_OWNER_DECISION", self.static)
        self.assertIn("HUMAN DECISION REQUIRED", self.runtime)

    def test_placeholders_are_intentional_and_have_described_purposes(self):
        for text in (self.static, self.runtime):
            with self.subTest(title=text.splitlines()[0]):
                placeholders = re.findall(r"{{([^{}]+)}}", text)
                self.assertTrue(placeholders)
                self.assertTrue(all(value.strip() for value in placeholders))
                self.assertNotRegex(text, r"{{\s*}}|TODO|TBD|TEMP(?:ORARY)?_MARKER")
                self.assertIn("请将 `{{...}}` 占位符替换为当前任务", text)

    def test_templates_do_not_embed_current_project_state_or_default_research(self):
        forbidden = (
            "foundation_v1",
            "4191024c5eef9c1d5332a3b2c76f70a252be9e6f",
            "147 / 147",
            "F4 / Step 4",
            "paper",
            "research",
            "论文",
            "研究实验",
        )
        for text in (self.static, self.runtime):
            for value in forbidden:
                with self.subTest(title=text.splitlines()[0], forbidden=value):
                    self.assertNotIn(value, text)

    def test_readme_template_links_resolve_and_document_provenance(self):
        for readme_path in (README_EN, README_ZH):
            text = readme_path.read_text(encoding="utf-8")
            for relative, source_hash in (
                ("templates/static_prompt_zh.md", STATIC_SOURCE_SHA256),
                ("templates/runtime_prompt_zh.md", RUNTIME_SOURCE_SHA256),
            ):
                with self.subTest(readme=readme_path.name, relative=relative):
                    self.assertIn(f"]({relative})", text)
                    self.assertTrue((ROOT / relative).is_file())
                    self.assertIn(source_hash, text)
            self.assertIn("Framework v1.2", text)

    def test_regression_reads_only_tracked_local_templates(self):
        self.assertEqual(STATIC_TEMPLATE.parent, ROOT / "templates")
        self.assertEqual(RUNTIME_TEMPLATE.parent, ROOT / "templates")
        self.assertTrue(self.static)
        self.assertTrue(self.runtime)


if __name__ == "__main__":
    unittest.main()
