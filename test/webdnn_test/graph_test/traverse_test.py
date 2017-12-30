from nose import with_setup

from webdnn.graph.attribute import Attribute
from webdnn.graph.graph import Graph
from webdnn.graph.node import Node
from webdnn.graph.operator import Operator
from webdnn.graph.order import OrderNC
from webdnn.graph.traverse import check_attribute_match, check_node_type_match, search_sub_structure, \
    filter_nodes, listup_operators, listup_variables, listup_nodes, sort_nodes
from webdnn.graph.variable import Variable

graph = None
op1 = None
op2 = None
op3 = None
v0 = None
v1 = None
v2 = None
v3 = None


class TestAttribute1(Attribute):
    pass


class TestAttribute2(Attribute):
    pass


# noinspection PyAbstractClass
class TestOperator(Operator):
    pass


def setup_graph_sequential():
    """
    generate sequential structure

    v0 --[op1]--> v1 --[op2]--> v2 --[op3]--> v3

    """
    global graph, op1, op2, op3
    global v0, v1, v2, v3

    v0 = Variable((1, 1), OrderNC)
    op1 = Operator("op1")
    v1 = Variable((1, 2), OrderNC)
    op2 = TestOperator("op2")
    v2 = Variable((1, 3), OrderNC)
    op3 = Operator("op3")
    v3 = Variable((1, 4), OrderNC)

    op1.append_input("v0", v0)
    op1.append_output("v1", v1)
    op2.append_input("v1", v1)
    op2.append_output("v2", v2)
    op3.append_input("v2", v2)
    op3.append_output("v3", v3)

    graph = Graph([v0], [v3])


def setup_graph_residual():
    """
    generate residual structure

    v0 --[op1]--> v1 -+----------------+--[op3]--> v3
                      |                |
                      +--[op2]--> v2 --+
    """
    global graph, op1, op2, op3
    global v0, v1, v2, v3

    v0 = Variable((1, 1), OrderNC)
    op1 = Operator("op1")
    v1 = Variable((1, 2), OrderNC)
    op2 = TestOperator("op2")
    v2 = Variable((1, 3), OrderNC)
    op3 = Operator("op3")
    v3 = Variable((1, 4), OrderNC)

    op1.append_input("v0", v0)
    op1.append_output("v1", v1)

    op2.append_input("v1", v1)
    op2.append_output("v2", v2)

    op3.append_input("v1", v1)
    op3.append_input("v2", v2)
    op3.append_output("v3", v3)

    graph = Graph([v0], [v3])


@with_setup(setup_graph_sequential)
def test_check_attribute_match():
    global op1, op2

    op1.attributes.add(TestAttribute1(op2))
    op2.attributes.add(TestAttribute2(op2))

    assert check_attribute_match(op1, TestAttribute1)
    assert not check_attribute_match(op2, TestAttribute1)


@with_setup(setup_graph_sequential)
def test_check_node_type_match():
    global op1, op2

    assert not check_node_type_match(op1, TestOperator)
    assert check_node_type_match(op2, TestOperator)
    assert check_node_type_match(op2, Operator)


@with_setup(setup_graph_sequential)
def test_search_sub_structure():
    global graph, op1, op2, op3, v1, v2

    matches = search_sub_structure(graph, [Operator, Variable, Operator])
    assert len(matches) == 2
    assert tuple(matches[0]) == (op1, v1, op2)
    assert tuple(matches[1]) == (op2, v2, op3)


@with_setup(setup_graph_sequential)
def test_search_sub_structure_full():
    global graph, op1, op2, op3, v1, v2

    matches = search_sub_structure(graph, [Operator, Variable, Operator, Variable, Operator])
    assert len(matches) == 1
    assert tuple(matches[0]) == (op1, v1, op2, v2, op3)


@with_setup(setup_graph_sequential)
def test_filter_nodes():
    global graph, op1

    op1.attributes.add(TestAttribute1(op1))
    op2.attributes.add(TestAttribute1(op2))

    ops = filter_nodes([op1, op2, op3], TestAttribute1)
    assert tuple(ops) == (op1, op2)


@with_setup(setup_graph_sequential)
def test_listup_nodes():
    global graph, op1, op2, op3, v0, v1, v2, v3
    nodes = listup_nodes(graph)

    assert tuple(nodes) == (v0, op1, v1, op2, v2, op3, v3)


def test_listup_nodes_hidden_output():
    v0 = Variable((1, 1), OrderNC)
    op1 = Operator("op1")
    v1 = Variable((1, 2), OrderNC)
    op2 = TestOperator("op2")
    v2 = Variable((1, 3), OrderNC)

    op1.append_input("v0", v0)
    op1.append_output("v1", v1)
    op2.append_input("v1", v1)
    op2.append_output("v2", v2)

    graph = Graph([v0], [v1, v2])  # outputs hidden variable

    nodes = listup_nodes(graph)

    assert tuple(nodes) == (v0, op1, v1, op2, v2), str(nodes)


@with_setup(setup_graph_sequential)
def test_listup_operators():
    global graph, op1, op2, op3
    ops = listup_operators(graph)

    assert tuple(ops) == (op1, op2, op3)


@with_setup(setup_graph_sequential)
def test_listup_variables():
    global graph, v0, v1, v2, v3
    variables = listup_variables(graph)

    assert tuple(variables) == (v0, v1, v2, v3)


@with_setup(setup_graph_residual)
def test_listup_nodes_residual():
    global graph, op1, op2, op3, v0, v1, v2, v3
    nodes = listup_nodes(graph)

    assert tuple(nodes) == (v0, op1, v1, op2, v2, op3, v3)


@with_setup(setup_graph_residual)
def test_listup_operators_residual():
    global graph, op1, op2, op3
    ops = listup_operators(graph)

    assert tuple(ops) == (op1, op2, op3)


@with_setup(setup_graph_residual)
def test_listup_variables_residual():
    global graph, v0, v1, v2, v3
    variables = listup_variables(graph)

    assert tuple(variables) == (v0, v1, v2, v3)


def test_sort_nodes():
    v1 = Node(name="n1")
    v2 = Node(name="n2")
    v3 = Node(name="n3")

    assert tuple(sort_nodes([v2, v3, v1])) == (v1, v2, v3)


def test_ignore_internal_bound_flag():
    #     +-2-3-4-5-+
    #   1-+         +-6-
    #     +---------+
    n1 = Node("n1")
    n2 = Node("n2")
    n3 = Node("n3")
    n4 = Node("n4")
    n5 = Node("n5")
    n6 = Node("n6")

    n2.append_prev(n1)
    n3.append_prev(n2)
    n4.append_prev(n3)
    n5.append_prev(n4)
    n6.append_prev(n1)
    n6.append_prev(n5)

    # noinspection PyTypeChecker
    graph = Graph([n1, n3], [n4, n6])

    result = listup_nodes(graph, ignore_internal_input_bound=False, ignore_internal_output_bound=False)
    assert len(result) == 4 and set(result) == {n1, n3, n4, n6}
    assert result.index(n1) < result.index(n6)
    assert result.index(n3) < result.index(n4)

    result = listup_nodes(graph, ignore_internal_input_bound=False, ignore_internal_output_bound=True)
    assert len(result) == 5 and set(result) == {n1, n3, n4, n5, n6}
    assert result.index(n1) < result.index(n6)
    assert result.index(n3) < result.index(n4)
    assert result.index(n4) < result.index(n5)
    assert result.index(n5) < result.index(n6)

    result = listup_nodes(graph, ignore_internal_input_bound=True, ignore_internal_output_bound=False)
    assert len(result) == 5 and set(result) == {n1, n2, n3, n4, n6}
    assert result.index(n1) < result.index(n2)
    assert result.index(n2) < result.index(n3)
    assert result.index(n3) < result.index(n4)
    assert result.index(n1) < result.index(n6)

    result = listup_nodes(graph, ignore_internal_input_bound=True, ignore_internal_output_bound=True)
    assert len(result) == 6 and set(result) == {n1, n2, n3, n4, n5, n6}
    assert result.index(n1) < result.index(n2)
    assert result.index(n2) < result.index(n3)
    assert result.index(n3) < result.index(n4)
    assert result.index(n4) < result.index(n5)
    assert result.index(n5) < result.index(n6)
    assert result.index(n1) < result.index(n6)
