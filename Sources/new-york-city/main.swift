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

func getBestMapping(between graph1: Graph, and graph2: Graph) -> Mapping {
    var mapping = Mapping()
    var bestMapping = mapping
    
    var potentialNewCouples = mapping.getPotentialNewCouples(graph1: graph1, graph2: graph2)
    
    while (
        !potentialNewCouples.allSatisfy {
            var newMapping = Mapping()
            newMapping.couples.insert($0)
            newMapping.couples.formUnion(mapping.couples)
            
            return newMapping.score(between: graph1, and: graph2) <= mapping.score(between: graph1, and: graph2) && mapping.potentialNewMatchingEdges(with: $0, between: graph1, and: graph2).isEmpty
        }
    ) {
        mapping.couples.insert(potentialNewCouples.randomElement()!)
        
        if mapping.score(between: graph1, and: graph2) > bestMapping.score(between: graph1, and: graph2) {
            bestMapping = mapping
        }
        
        potentialNewCouples = mapping.getPotentialNewCouples(graph1: graph1, graph2: graph2)
    }
    return bestMapping
}

let mapping = getBestMapping(between: graph1, and: graph2)

let formatter = NumberFormatter()
formatter.numberStyle = .percent
formatter.minimumFractionDigits = 2

print("Similarity: \(formatter.string(from: mapping.similarity(between: graph1, and: graph2) as NSNumber)!)")
print(mapping)
