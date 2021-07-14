import ast
from ast import Call, FunctionDef, ClassDef
from typing import Dict, Set, Optional, Any
from loguru import logger
from pyvis.network import Network


def main():
    # with open("ast_example.py", "r") as source:
    #     tree = ast.parse(source.read())

    tree = ast.parse(
        """\
class Test:
    def e() -> float:
        return d()

    def f() -> float:
        return d()

class Test2:
    def g() -> float:
        return d()

def a(b: int, c: int=3) -> float:
   return 0.0

def d() -> float:
    r = a(1, 2) + a(3, 4)
    return r
"""
    )
    # print(ast.dump(tree, indent=4))

    analyzer = Analyzer()
    analyzer.visit(tree)
    analyzer.construct_graph()
    analyzer.plot()
    print()


class Analyzer(ast.NodeVisitor):
    def __init__(self):
        # INFORMATION GATHERING
        # Line belongs to class
        self.line_belongs_to_class: Dict[int, str] = {}
        # Line belongs to function
        self.line_belongs_to_function: Dict[int, str] = {}
        # Function call in line - the name of the function and the line number
        self.function_call_in_line: Dict[int, Set[str]] = {}

        # What functions this class has
        self.class_has_functions: Dict[str, Set[str]] = {}
        # Which class the function is in
        self.function_in_which_class: Dict[str, str] = {}

        # GRAPH RECONSTRUCTION
        # Which function this function is called from
        self.function_called_from: Dict[str, Set[str]] = {}
        # Which function this function calls
        self.function_calls: Dict[str, Set[str]] = {}

    @staticmethod
    def _add(my_dict: Dict, key: Any, value: Any):
        if key not in my_dict:
            my_dict[key] = set()
        my_dict[key].add(value)

    def visit(self, node):
        if isinstance(node, Call):
            self._add(self.function_call_in_line, node.lineno, node.func.id)
            logger.info(f"Line {node.lineno} calls function '{node.func.id}'")

        # Which line does which function belong to?
        if isinstance(node, FunctionDef):
            self.function_calls[node.name] = set()
            logger.info(f"Function definition '{node.name}' in line {node.lineno}")
            for i in range(node.lineno, node.end_lineno + 1):
                self.line_belongs_to_function[i] = node.name

            if node.lineno in self.line_belongs_to_class:
                class_name = self.line_belongs_to_class[node.lineno]
                self.function_in_which_class[node.name] = class_name
                self.class_has_functions[class_name].add(node.name)

        if isinstance(node, ClassDef):
            self.class_has_functions[node.name] = set()
            for i in range(node.lineno, node.end_lineno + 1):
                self.line_belongs_to_class[i] = node.name

        return super().visit(node)

    def construct_graph(self):
        for call_line, function_call_names in self.function_call_in_line.items():
            for function_call_name in function_call_names:
                callee_function = self.line_belongs_to_function[call_line]

                self._add(self.function_called_from, function_call_name, callee_function)
                self._add(self.function_calls, callee_function, function_call_name)

    def plot(self):
        nt = Network('500px', '500px', directed=True)

        def create_node_if_not_exists(
            graph: Network,
            node_name: str,
            node_group_name: Optional[str] = None,
        ):
            if node_name not in graph.nodes:
                graph.add_node(node_name)
                # Style them based on group
                if node_group_name is not None:
                    nt.node_map[node_name]["group"] = node_group_name
                    nt.node_map[node_name]["title"] = node_group_name
                else:
                    nt.node_map[node_name]["group"] = "No class"

        for caller, functions_being_called in self.function_calls.items():
            group_name = self.function_in_which_class.get(caller)
            create_node_if_not_exists(nt, caller, group_name)
            for function_being_called in functions_being_called:
                group_name2 = self.function_in_which_class.get(function_being_called)
                create_node_if_not_exists(nt, function_being_called, group_name2)
                nt.add_edge(caller, function_being_called)
                logger.info(f"{caller} - {function_being_called}")

        nt.show("nx.html")


if __name__ == "__main__":
    main()
    # Include library function calls?
    # group class functions into one big blob?
