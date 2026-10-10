import re
from typing import List
from nl2code.backend.app.llm.base import LLMProvider
from nl2code.backend.app.models.ir import (
    IntermediateRepresentation,
    IntentParseResult,
    InputParam,
    OutputParam,
    ComplexityTarget,
    TestCase
)

class MockLLMProvider(LLMProvider):
    """
    Deterministic Mock LLM Provider for unit tests, offline development,
    and guaranteed zero-dependency demonstration of the 4 core demo prompts.
    """

    async def parse_intent(self, prompt: str) -> IntentParseResult:
        p_lower = prompt.lower()
        if "frequent" in p_lower or "top k" in p_lower:
            return IntentParseResult(
                task="Find the k most frequent elements in an integer array",
                target_language="python",
                identified_inputs=[{"name": "nums", "type": "list"}, {"name": "k", "type": "int"}],
                identified_outputs={"type": "list", "description": "List of k most frequent elements"},
                constraints=["1 <= nums.length <= 10^5", "k is in range [1, unique elements]"],
                edge_cases=["k equals array length", "All elements have identical frequency", "Single element array"],
                suggested_function_name="top_k_frequent"
            )
        elif "palindrome" in p_lower:
            return IntentParseResult(
                task="Determine whether a string is a palindrome ignoring punctuation and casing",
                target_language="cpp",
                identified_inputs=[{"name": "s", "type": "string"}],
                identified_outputs={"type": "bool", "description": "True if palindrome, False otherwise"},
                constraints=["0 <= s.length <= 2 * 10^5", "String contains ASCII characters"],
                edge_cases=["Empty string", "String with only punctuation", "Single character"],
                suggested_function_name="is_palindrome"
            )
        elif "interval" in p_lower or "merge" in p_lower:
            return IntentParseResult(
                task="Merge all overlapping intervals and return non-overlapping intervals covering all inputs",
                target_language="java",
                identified_inputs=[{"name": "intervals", "type": "list"}],
                identified_outputs={"type": "list", "description": "Array of merged intervals"},
                constraints=["1 <= intervals.length <= 10^4", "intervals[i].length == 2"],
                edge_cases=["No overlaps", "All intervals overlap into one", "Intervals already sorted"],
                suggested_function_name="merge_intervals"
            )
        elif "debounce" in p_lower:
            return IntentParseResult(
                task="Create a debounced version of a function that delays execution until N milliseconds have elapsed",
                target_language="javascript",
                identified_inputs=[{"name": "delay_ms", "type": "int"}],
                identified_outputs={"type": "any", "description": "Debounce controller status"},
                constraints=["delay_ms >= 0"],
                edge_cases=["Zero delay", "Multiple immediate invocations"],
                suggested_function_name="debounce_tester"
            )
        else:
            clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', prompt[:20].strip().lower()).strip('_') or "solve"
            return IntentParseResult(
                task=prompt.strip(),
                target_language="python",
                identified_inputs=[{"name": "data", "type": "list"}],
                identified_outputs={"type": "list", "description": "Computed algorithmic result"},
                constraints=["Inputs fit in standard memory"],
                edge_cases=["Empty input"],
                suggested_function_name=clean_name
            )

    async def build_ir(self, intent: IntentParseResult, language: str) -> IntermediateRepresentation:
        p_lower = intent.task.lower()
        target_lang = language.lower() if language else intent.target_language.lower()

        if "frequent" in p_lower or "top k" in p_lower:
            return IntermediateRepresentation(
                task_description=intent.task,
                target_language=target_lang,
                function_name="top_k_frequent",
                signature="def top_k_frequent(nums: list, k: int) -> list:",
                inputs=[
                    InputParam(name="nums", type="list", description="Array of numbers"),
                    InputParam(name="k", type="int", description="Number of frequent elements to return")
                ],
                outputs=OutputParam(type="list", description="The k most frequent elements"),
                constraints=intent.constraints,
                edge_cases=intent.edge_cases,
                complexity_target=ComplexityTarget(
                    time_complexity="O(n log k)",
                    space_complexity="O(n)",
                    explanation="Counting frequencies takes O(n) hash map space. Min-heap of size k takes O(n log k) time."
                ),
                test_cases=[
                    TestCase(
                        id=1,
                        name="Standard Case",
                        input_args={"nums": [1, 1, 1, 2, 2, 3], "k": 2},
                        expected_output=[1, 2],
                        is_edge_case=False,
                        description="General frequency ranking with distinct counts"
                    ),
                    TestCase(
                        id=2,
                        name="Single Element",
                        input_args={"nums": [1], "k": 1},
                        expected_output=[1],
                        is_edge_case=True,
                        description="Boundary condition of single element array"
                    ),
                    TestCase(
                        id=3,
                        name="Uniform Frequencies",
                        input_args={"nums": [4, 5, 6], "k": 1},
                        expected_output=[4],
                        is_edge_case=False,
                        description="Elements all appear once"
                    )
                ]
            )
        elif "palindrome" in p_lower:
            return IntermediateRepresentation(
                task_description=intent.task,
                target_language=target_lang,
                function_name="is_palindrome",
                signature="bool is_palindrome(std::string s)" if target_lang == "cpp" else "def is_palindrome(s: str) -> bool:",
                inputs=[InputParam(name="s", type="string", description="Input string to evaluate")],
                outputs=OutputParam(type="bool", description="True if alphanumeric characters form palindrome"),
                constraints=intent.constraints,
                edge_cases=intent.edge_cases,
                complexity_target=ComplexityTarget(
                    time_complexity="O(n)",
                    space_complexity="O(1)",
                    explanation="Two-pointer comparison from both ends directly without additional buffer allocation."
                ),
                test_cases=[
                    TestCase(
                        id=1,
                        name="Valid Palindrome with punctuation",
                        input_args={"s": "A man, a plan, a canal: Panama"},
                        expected_output=True,
                        is_edge_case=False,
                        description="Complex sentence with spaces and punctuation"
                    ),
                    TestCase(
                        id=2,
                        name="Invalid Palindrome",
                        input_args={"s": "race a car"},
                        expected_output=False,
                        is_edge_case=False,
                        description="Non-symmetric string"
                    ),
                    TestCase(
                        id=3,
                        name="Empty or Whitespace Only",
                        input_args={"s": "   "},
                        expected_output=True,
                        is_edge_case=True,
                        description="Boundary empty alphanumeric string evaluates to true"
                    )
                ]
            )
        elif "interval" in p_lower or "merge" in p_lower:
            return IntermediateRepresentation(
                task_description=intent.task,
                target_language=target_lang,
                function_name="merge_intervals",
                signature="public int[][] merge_intervals(int[][] intervals)" if target_lang == "java" else "def merge_intervals(intervals: list) -> list:",
                inputs=[InputParam(name="intervals", type="list", description="Array of interval pairs [start, end]")],
                outputs=OutputParam(type="list", description="Merged non-overlapping intervals"),
                constraints=intent.constraints,
                edge_cases=intent.edge_cases,
                complexity_target=ComplexityTarget(
                    time_complexity="O(n log n)",
                    space_complexity="O(n)",
                    explanation="Sorting intervals by start time takes O(n log n). Linear merge pass takes O(n)."
                ),
                test_cases=[
                    TestCase(
                        id=1,
                        name="Overlapping intervals",
                        input_args={"intervals": [[1, 3], [2, 6], [8, 10], [15, 18]]},
                        expected_output=[[1, 6], [8, 10], [15, 18]],
                        is_edge_case=False,
                        description="Standard overlapping pair [1,3] and [2,6]"
                    ),
                    TestCase(
                        id=2,
                        name="Adjacent intervals",
                        input_args={"intervals": [[1, 4], [4, 5]]},
                        expected_output=[[1, 5]],
                        is_edge_case=True,
                        description="Intervals touch at boundary point 4"
                    )
                ]
            )
        elif "debounce" in p_lower:
            return IntermediateRepresentation(
                task_description=intent.task,
                target_language=target_lang,
                function_name="debounce_tester",
                signature="function debounce_tester(delay_ms)" if target_lang == "javascript" else "def debounce_tester(delay_ms: int):",
                inputs=[InputParam(name="delay_ms", type="int", description="Debounce delay in ms")],
                outputs=OutputParam(type="any", description="Execution confirmation"),
                constraints=intent.constraints,
                edge_cases=intent.edge_cases,
                complexity_target=ComplexityTarget(
                    time_complexity="O(1)",
                    space_complexity="O(1)",
                    explanation="Timer closure with clear and reset operates in constant time and space."
                ),
                test_cases=[
                    TestCase(
                        id=1,
                        name="Standard debounce delay",
                        input_args={"delay_ms": 100},
                        expected_output={"debounced": True, "delay": 100},
                        is_edge_case=False,
                        description="Valid delay initialization"
                    ),
                    TestCase(
                        id=2,
                        name="Zero delay debounce",
                        input_args={"delay_ms": 0},
                        expected_output={"debounced": True, "delay": 0},
                        is_edge_case=True,
                        description="Boundary condition of 0ms timer"
                    )
                ]
            )
        else:
            return IntermediateRepresentation(
                task_description=intent.task,
                target_language=target_lang,
                function_name=intent.suggested_function_name,
                signature=f"def {intent.suggested_function_name}(data: list) -> list:",
                inputs=[InputParam(name="data", type="list", description="Input collection")],
                outputs=OutputParam(type="list", description="Result collection"),
                constraints=intent.constraints,
                edge_cases=intent.edge_cases,
                complexity_target=ComplexityTarget(
                    time_complexity="O(n)",
                    space_complexity="O(n)",
                    explanation="Linear scan through data collection."
                ),
                test_cases=[
                    TestCase(
                        id=1,
                        name="Default case",
                        input_args={"data": [1, 2, 3]},
                        expected_output=[1, 2, 3],
                        is_edge_case=False,
                        description="Identity check for generalized function"
                    )
                ]
            )

    async def generate_code(self, ir: IntermediateRepresentation, language: str) -> str:
        lang = language.lower() if language else ir.target_language.lower()
        fn = ir.function_name

        if fn == "top_k_frequent":
            if lang == "python":
                return (
                    "from collections import Counter\n\n"
                    "def top_k_frequent(nums: list, k: int) -> list:\n"
                    "    \"\"\"\n"
                    "    Returns the k most frequent elements in nums.\n"
                    "    Time Complexity: O(n log k)\n"
                    "    Space Complexity: O(n)\n"
                    "    \"\"\"\n"
                    "    count = Counter(nums)\n"
                    "    return [item for item, _ in count.most_common(k)]\n"
                )
            elif lang == "javascript":
                return (
                    "function top_k_frequent(nums, k) {\n"
                    "    const counts = {};\n"
                    "    for (const n of nums) counts[n] = (counts[n] || 0) + 1;\n"
                    "    const sorted = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);\n"
                    "    return sorted.slice(0, k).map(Number);\n"
                    "}\n"
                )
        elif fn == "is_palindrome":
            if lang == "cpp":
                return (
                    "bool is_palindrome(std::string s) {\n"
                    "    int left = 0, right = s.length() - 1;\n"
                    "    while (left < right) {\n"
                    "        while (left < right && !std::isalnum(s[left])) left++;\n"
                    "        while (left < right && !std::isalnum(s[right])) right--;\n"
                    "        if (std::tolower(s[left]) != std::tolower(s[right])) return false;\n"
                    "        left++;\n"
                    "        right--;\n"
                    "    }\n"
                    "    return true;\n"
                    "}\n"
                )
            elif lang == "python":
                return (
                    "def is_palindrome(s: str) -> bool:\n"
                    "    cleaned = [c.lower() for c in s if c.isalnum()]\n"
                    "    return cleaned == cleaned[::-1]\n"
                )
        elif fn == "merge_intervals":
            if lang == "java":
                return (
                    "    public static int[][] merge_intervals(int[][] intervals) {\n"
                    "        if (intervals.length <= 1) return intervals;\n"
                    "        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));\n"
                    "        List<int[]> result = new ArrayList<>();\n"
                    "        int[] curr = intervals[0];\n"
                    "        result.add(curr);\n"
                    "        for (int[] interval : intervals) {\n"
                    "            if (interval[0] <= curr[1]) {\n"
                    "                curr[1] = Math.max(curr[1], interval[1]);\n"
                    "            } else {\n"
                    "                curr = interval;\n"
                    "                result.add(curr);\n"
                    "            }\n"
                    "        }\n"
                    "        return result.toArray(new int[result.size()][]);\n"
                    "    }\n"
                )
            elif lang == "python":
                return (
                    "def merge_intervals(intervals: list) -> list:\n"
                    "    if not intervals:\n"
                    "        return []\n"
                    "    intervals.sort(key=lambda x: x[0])\n"
                    "    merged = [intervals[0]]\n"
                    "    for current in intervals[1:]:\n"
                    "        prev = merged[-1]\n"
                    "        if current[0] <= prev[1]:\n"
                    "            prev[1] = max(prev[1], current[1])\n"
                    "        else:\n"
                    "            merged.append(current)\n"
                    "    return merged\n"
                )
        elif fn == "debounce_tester":
            if lang == "javascript":
                return (
                    "function debounce_tester(delay_ms) {\n"
                    "    let timeoutId = null;\n"
                    "    const debounce = (fn) => {\n"
                    "        return (...args) => {\n"
                    "            clearTimeout(timeoutId);\n"
                    "            timeoutId = setTimeout(() => fn(...args), delay_ms);\n"
                    "        };\n"
                    "    };\n"
                    "    return { debounced: true, delay: delay_ms };\n"
                    "}\n"
                )

        # Fallback default code
        if lang == "python":
            return f"def {fn}(data: list) -> list:\n    return list(data)\n"
        elif lang == "javascript":
            return f"function {fn}(data) {{\n    return data;\n}}\n"
        elif lang == "cpp":
            return f"#include <vector>\nstd::vector<int> {fn}(std::vector<int> data) {{\n    return data;\n}}\n"
        else:
            return f"public class Solution {{\n    public int[] {fn}(int[] data) {{\n        return data;\n    }}\n}}\n"

    async def repair_code(
        self,
        code: str,
        errors: List[str],
        ir: IntermediateRepresentation,
        language: str,
        attempt: int
    ) -> str:
        # Repaired version delivers the correct working code for the target IR
        return await self.generate_code(ir, language)
