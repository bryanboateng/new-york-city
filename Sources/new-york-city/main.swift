import Algorithms
import Foundation

let graph1: Graph = {
    var graph = Graph()
    graph.add(vertex: "a", withLabels: ["beam", "I"])
    graph.add(vertex: "b", withLabels: ["beam", "I"])
    graph.add(vertex: "c", withLabels: ["beam", "I"])
    graph.add(vertex: "d", withLabels: ["beam", "I"])
    graph.add(vertex: "e", withLabels: ["wall"])
    graph.add(vertex: "f", withLabels: ["wall"])
    graph.addEdge(from: "a", to: "e", withLabels: ["on"])
    graph.addEdge(from: "b", to: "e", withLabels: ["on"])
    graph.addEdge(from: "c", to: "f", withLabels: ["on"])
    graph.addEdge(from: "d", to: "f", withLabels: ["on"])
    graph.addEdge(from: "a", to: "b", withLabels: ["next-to"])
    graph.addEdge(from: "b", to: "c", withLabels: ["next-to"])
    graph.addEdge(from: "c", to: "d", withLabels: ["next-to"])
    return graph
}()

let graph2: Graph = {
    var graph = Graph()
    graph.add(vertex: "1", withLabels: ["beam", "U"])
    graph.add(vertex: "2", withLabels: ["beam", "U"])
    graph.add(vertex: "3", withLabels: ["beam", "U"])
    graph.add(vertex: "4", withLabels: ["beam", "U"])
    graph.add(vertex: "5", withLabels: ["wall"])
    graph.addEdge(from: "1", to: "5", withLabels: ["on"])
    graph.addEdge(from: "2", to: "5", withLabels: ["on"])
    graph.addEdge(from: "3", to: "5", withLabels: ["on"])
    graph.addEdge(from: "4", to: "5", withLabels: ["on"])
    graph.addEdge(from: "1", to: "2", withLabels: ["next-to"])
    graph.addEdge(from: "2", to: "3", withLabels: ["next-to"])
    graph.addEdge(from: "3", to: "4", withLabels: ["next-to"])
    return graph
}()

let mapping = [("a", "1"), ("b", "2"), ("c", "3"), ("d", "4"), ("e", "5"), ("f", "5")]

func similarity(between graph1: Graph, and graph2: Graph, using mapping: [(String, String)]) -> Double {
    return Double(
        matchedLabeledVertices(of: graph1, in: graph2, using: mapping).count
        + matchedLabeledVertices(of: graph2, in: graph1, using: mapping).count
        + matchedLabeledEdges(of: graph1, in: graph2, using: mapping).count
        + matchedLabeledEdges(of: graph2, in: graph1, using: mapping).count
        - splitCount(of: mapping)
    )
    /
    Double(
        graph1.labeledVertices.count
        + graph1.labeledEdges.count
        + graph2.labeledVertices.count
        + graph2.labeledEdges.count
    )
}

func applyMapping(_ mapping: [(String, String)], to vertex: String) -> [String] {
    return mapping
        .filter { $0 == vertex || $1 == vertex }
        .map { $0 == vertex ? $1 : $0 }
}

func matchedLabeledVertices(of graph1: Graph, in graph2: Graph, using mapping: [(String, String)]) -> Set<LabeledVertex> {
    graph1.labeledVertices
        .filter { labeledVertex in
            let mappedVertices = applyMapping(mapping, to: labeledVertex.vertex)
            return graph2.labeledVertices
                .filter { labeledVertex2 in
                    mappedVertices.contains(labeledVertex2.vertex)
                }
                .contains { labeledVertex2 in
                    labeledVertex2.label == labeledVertex.label
                }
        }
}

func matchedLabeledEdges(of graph1: Graph, in graph2: Graph, using mapping: [(String, String)]) -> Set<LabeledEdge> {
    graph1.labeledEdges
        .filter { labeledEdge in
            let mappedOriginVertices = applyMapping(mapping, to: labeledEdge.origin)
            let mappedDestinationVertices = applyMapping(mapping, to: labeledEdge.destination)
            
            return graph2.labeledEdges
                .filter { labeledEdge2 in
                    mappedOriginVertices.contains(labeledEdge2.origin)
                    && mappedDestinationVertices.contains(labeledEdge2.destination)
                }
                .contains { labeledEdge2 in
                    labeledEdge2.label == labeledEdge.label
                }
        }
}

func splitCount(of mapping: [(String, String)]) -> Int {
    let verticesWithCount: [String: Int] = {
        var verticesWithCount: [String: Int] = [:]
        mapping
            .flatMap { [$0, $1] }
            .forEach { verticesWithCount[$0, default: 0] += 1 }
        return verticesWithCount
    }()
    
    return verticesWithCount
        .filter {
            $0.value >= 2
        }
        .count
}


let allPossibleMappings = product(graph1.vertices, graph2.vertices)
    .combinations(ofCount: 0...)

let bestMapping = allPossibleMappings.max {
    similarity(between: graph1, and: graph2, using: $0) < similarity(between: graph1, and: graph2, using: $1)
}

print(bestMapping!)
