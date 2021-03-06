#!/usr/bin/python
# simplify.py, (C) 2007-2009 Yrjo Kari-Koskinen <ykk@peruna.fi>
#
# This program is licensed under Version 2 of the GPL.

# Simplify debts by minimizing transactions.
# 
# Use following input from stdin:
#
# * -> Foo: 15.50
# = everybody ows Foo 15.50 units
#
# Foo -> Bar: 10.00
# = Foo ows Bar 10.00 units
#
# Zot
# = Zot has no direct debts but is to be included in "everybody"


import sys
import re

def printEdges(edges):
    for edge in edges:
        edge.normalize()
        print edge.toString()

def addWeight(weights, nodeName, weightDelta):
    try:
        oldWeight = weights[nodeName]
    except KeyError:
        oldWeight = 0
    weights[nodeName] = oldWeight + weightDelta

def sort(weights):
    weightItems = [(value, key) for key, value in weights.items()]
    weightItems.sort()
    return weightItems

def getNodeWeights(edges):
    weights = {}
    for edge in edges:
        addWeight(weights, edge.endNode, edge.weight)
        addWeight(weights, edge.startNode, -1 * edge.weight)
    return weights

def findGreaterWeight(weightComp, weights):
    for node, weight in weights.iteritems():
        if weight > weightComp:
            return node
    raise NodeError, 'Edge not found'    

class NodeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class EdgeException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

def weightsToEdges(sortedWeights, weights):
    i = 0
    edges = []
    input = 0
    while i+1 < len(sortedWeights):
        currentNode = sortedWeights[i][1]
        currentWeight = weights[currentNode]
        delta = input - currentWeight
        if currentWeight < 0:
            try:
                node = findGreaterWeight(delta, weights)
                edges.append(Edge(currentNode, node, delta))
                weights[node] -= delta
                input = 0
                i += 1
                continue
            except NodeError:
                pass
        edges.append(Edge(currentNode, sortedWeights[i+1][1], delta))
        input = delta
        i += 1
    return edges

def removeZeroWeights(w):
    i = 0
    while i < len(w):
        if w[i][0] == 0:
            w.pop(i)
        else:
            i += 1


def splitStarNodes(edges, emptyNodes):
    nodes = emptyNodes
    for edge in edges:
        if edge.startNode != "*":
            nodes.append(edge.startNode)
        if edge.endNode != "*":
            nodes.append(edge.endNode)
    uniqueNodes = uniqueList(nodes)
    if verbose:
        print "Found these", len(uniqueNodes), "unique nodes:", uniqueNodes
    
    i = 0
    while i < len(edges):
        if edges[i].startNode == "*": # * -> Foo: 10
            for node in uniqueNodes:
                if node != edges[i].endNode:
                    edges.append(Edge(node, edges[i].endNode,
                                      edges[i].weight/len(uniqueNodes)))
            edges.pop(i)
        elif edges[i].endNode == "*": # Foo -> *: 10
            for node in uniqueNodes:
                if node != edges[i].startNode:
                    edges.append(Edge(edges[i].startNode, node,
                                      edges[i].weight/len(uniqueNodes)))
            edges.pop(i)
        else:
            i += 1
    return edges

def uniqueList(list):
    set = {}
    map(set.__setitem__, list, [])
    return set.keys()

searchComment = re.compile("^(#| *$)");
searchEdge = re.compile("(\w+|\*) *-> *(\w+|\*): *([0-9]+(\.[0-9]+)?)")
searchNode = re.compile("^(\w+)$")

def parseEdge(line):
    m = searchEdge.match(line)
    if m != None:
        startNode = m.group(1)
        endNode = m.group(2)
        weight = float(m.group(3))
        if startNode != endNode:
            return Edge(startNode, endNode, weight)
    raise EdgeException, "Invalid input line"

class Edge:
    def __init__(self, startNode, endNode, weight):
        self.startNode = startNode
        self.endNode = endNode
        self.weight = weight
 
    def toString(self):
        return self.startNode + " -> " + self.endNode + ": " + str(self.weight)

    def otherNode(self, nodeName):
        if self.startNode == nodeName:
            return self.endNode
        else:
            return self.startNode
    
    def equalEdges(self, other):
        if self.startNode == other.startNode and self.endNode == other.endNode:
            return 1
        elif self.startNode == other.endNode and self.endNode == other.startNode:
            return -1
        else:
            return 0

    def normalize(self):
        if self.weight < 0:
            self.weight *= -1
            tempNode = self.startNode
            self.startNode = self.endNode
            self.endNode = tempNode


edges = []
emptyNodes = []
i = 1
for line in sys.stdin:
    try:
        edges.append(parseEdge(line))
    except EdgeException:
        if searchNode.match(line):
            emptyNodes.append(line.rstrip())
        elif searchComment.match(line):
            pass
        else: 
            print >> sys.stderr, "Invalid input on line", i, ": " + line.rstrip()
            exit(1)
    i += 1

# TODO: set verbose with a parameter
verbose = False
edges = splitStarNodes(edges, emptyNodes)

weights = getNodeWeights(edges)
sortedWeights = sort(weights)
removeZeroWeights(sortedWeights)
# TODO: assert weight sum == zero
if verbose:
    print "Node weights: ", sortedWeights

edges = weightsToEdges(sortedWeights, weights)
# TODO: assert edge sum == zero
printEdges(edges)
