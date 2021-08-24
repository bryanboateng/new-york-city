extension Array {
    func maxima<T: Comparable>(using scoreFunction: (Element) -> T) -> [Element] {
        let scoredElements = self
            .map { element in
                (element, scoreFunction(element))
            }
        
        let maxScore = scoredElements
            .map { (element, score) in
                score
            }
            .max()!
        
        return scoredElements
            .filter { (element, score) in
                score == maxScore
            }
            .map { (element, score) in
                element
            }
    }
}
