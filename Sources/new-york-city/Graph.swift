struct Graph {
    private(set) var vertices = Set<String>()
    private(set) var labeledVertices = Set<LabeledVertex>()
    private(set) var labeledEdges = Set<LabeledEdge>()
        
    mutating func add(vertex: String, withLabels labels: [String]) {
        vertices.insert(vertex)
        for label in labels {
            labeledVertices.insert(LabeledVertex(vertex: vertex, label: label))
        }
    }
    
    mutating func addEdge(from vertex1: String, to vertex2: String, withLabels labels: [String]) {
        for label in labels {
            labeledEdges.insert(LabeledEdge(origin: vertex1, destination: vertex2, label: label))
        }
    }
}
