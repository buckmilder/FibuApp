import Foundation

/// Stable IDs are persisted; filenames preserve the mapping to the supplied texture archive.
enum FibuSkin: String, CaseIterable, Identifiable {
    case original, cloud, vanilla, tangerine, ocean, caramel, sunshine, mint, berry, peach, stitched, leopard
    var id: String { rawValue }
    var name: String { rawValue.capitalized }
    var sourceID: String {
        switch self {
        case .original: return "original"
        case .cloud: return "000"
        case .vanilla: return "001"
        case .tangerine: return "002"
        case .ocean: return "003"
        case .caramel: return "004"
        case .sunshine: return "005"
        case .mint: return "006"
        case .berry: return "007"
        case .peach: return "011"
        case .stitched: return "012"
        case .leopard: return "013"
        }
    }
    var textureName: String? { self == .original ? nil : "FibuSkin" + sourceID }
    var iconName: String {
        // No matching SVG was supplied for the embedded original or skin 013.
        self == .original || self == .leopard ? previewName : "SkinIcon" + sourceID
    }
    var previewName: String { "FibuPreview" + sourceID }
    static func saved(_ value: String) -> FibuSkin { FibuSkin(rawValue: value) ?? .original }
}
