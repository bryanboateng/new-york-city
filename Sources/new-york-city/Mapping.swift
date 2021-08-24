import Algorithms

struct Mapping {
    var couples = Set<Mapping.Couple>()
    
    var splitCount: Int {
        let verticesWithCount: [String: Int] = {
            var verticesWithCount: [String: Int] = [:]
            couples
                .flatMap { [$0.a, $0.b] }
                .forEach { verticesWithCount[$0, default: 0] += 1 }
            return verticesWithCount
        }()
        
        return verticesWithCount
            .filter {
                $0.value >= 2
            }
            .count
    }
    
    func map(vertex: String) -> [String] {
        return couples
            .filter { $0.a == vertex || $0.b == vertex }
            .map { $0.a == vertex ? $0.b : $0.a }
    }
    
    func score(between graph1: Graph, and graph2: Graph) -> Int {
        matchedLabeledVertices(of: graph1, in: graph2).count
        + matchedLabeledVertices(of: graph2, in: graph1).count
        + matchedLabeledEdges(of: graph1, in: graph2).count
        + matchedLabeledEdges(of: graph2, in: graph1).count
        - splitCount
    }
    
    func similarity(between graph1: Graph, and graph2: Graph) -> Double {
        return Double(score(between: graph1, and: graph2))
        /
        Double(
            graph1.labeledVertices.count
            + graph1.labeledEdges.count
            + graph2.labeledVertices.count
            + graph2.labeledEdges.count
        )
    }
    
    func matchedLabeledVertices(of graph1: Graph, in graph2: Graph) -> Set<LabeledVertex> {
        graph1.labeledVertices
            .filter { labeledVertex in
                let mappedVertices = map(vertex: labeledVertex.vertex)
                return graph2.labeledVertices
                    .filter { labeledVertex2 in
                        mappedVertices.contains(labeledVertex2.vertex)
                    }
                    .contains { labeledVertex2 in
                        labeledVertex2.label == labeledVertex.label
                    }
            }
    }
    
    func matchedLabeledEdges(of graph1: Graph, in graph2: Graph) -> Set<LabeledEdge> {
        graph1.labeledEdges
            .filter { labeledEdge in
                let mappedOriginVertices = map(vertex: labeledEdge.origin)
                let mappedDestinationVertices = map(vertex: labeledEdge.destination)
                
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
    
    func getPotentialNewCouples(graph1: Graph, graph2: Graph) -> [Mapping.Couple] {
        return product(graph1.vertices, graph2.vertices)
            .map {
                Mapping.Couple(a: $0.0, b: $0.1)
            }
            .filter {
                !couples.contains($0)
            }
            .maxima { couple -> Int in
                var newMapping = Mapping()
                newMapping.couples.insert(couple)
                newMapping.couples.formUnion(couples)
                return newMapping.score(between: graph1, and: graph2)
            }
            .maxima { couple -> Int in
                var newMapping = Mapping()
                newMapping.couples.insert(couple)
                newMapping.couples.formUnion(couples)
                return newMapping.potentialNewMatchingEdges(with: couple, between: graph1, and: graph2).count
            }
    }
    
    func potentialNewMatchingEdges(with newCouple: Mapping.Couple, between graph1: Graph, and graph2: Graph) -> Set<LabeledEdge>{
        let originGraph1Edges = potentialMatchingGraph1Edges(graph1: graph1, graph2: graph2, couple: newCouple, on: \.origin)
        let destinationGraph1Edges = potentialMatchingGraph1Edges(graph1: graph1, graph2: graph2, couple: newCouple, on: \.destination)
        let originGraph2Edges = potentialMatchingGraph2Edges(graph1: graph1, graph2: graph2, couple: newCouple, on: \.origin)
        let destinationGraph2Edges = potentialMatchingGraph2Edges(graph1: graph1, graph2: graph2, couple: newCouple, on: \.destination)
        
        var newMapping = Mapping()
        newMapping.couples.insert(newCouple)
        newMapping.couples.formUnion(couples)
        
        let alreadyMatchedEdges = newMapping.matchedLabeledEdges(of: graph1, in: graph2)
            .union(
                newMapping.matchedLabeledEdges(of: graph2, in: graph1)
            )
        
        return originGraph1Edges
            .union(destinationGraph1Edges)
            .union(originGraph2Edges)
            .union(destinationGraph2Edges)
            .subtracting(alreadyMatchedEdges)
    }
    
    func potentialMatchingGraph1Edges(graph1: Graph, graph2: Graph, couple: Mapping.Couple, on keyPath: KeyPath<LabeledEdge, String>) -> Set<LabeledEdge> {
        return graph1.labeledEdges
            .filter { labeledEdge in
                labeledEdge[keyPath: keyPath] == couple.a
            }
            .filter { labeledEdge in
                !graph2.labeledEdges
                    .filter{ labeledEdge2 in
                        labeledEdge2[keyPath: keyPath] == couple.b
                    }
                    .filter { labeledEdge2 in
                        labeledEdge.label == labeledEdge2.label
                    }
                    .isEmpty
            }
    }
    
    func potentialMatchingGraph2Edges(graph1: Graph, graph2: Graph, couple: Mapping.Couple, on keyPath: KeyPath<LabeledEdge, String>) -> Set<LabeledEdge> {
        return graph2.labeledEdges
            .filter { labeledEdge in
                labeledEdge[keyPath: keyPath] == couple.b
            }
            .filter { labeledEdge in
                !graph1.labeledEdges
                    .filter{ labeledEdge2 in
                        labeledEdge2[keyPath: keyPath] == couple.a
                    }
                    .filter { labeledEdge2 in
                        labeledEdge.label == labeledEdge2.label
                    }
                    .isEmpty
            }
    }
    
    struct Couple: Hashable, CustomStringConvertible {
        let a: String
        let b: String
        
        var description: String {
            "\(a) -> \(b)"
        }
    }
}

extension Mapping: CustomStringConvertible {
    var description: String {
        var description = ""
        for element in couples.sorted(by: { $0.a < $1.a}) {
            description += "\(element.a) -> \(element.b)\n"
        }
        return String(description.dropLast())
    }
}
