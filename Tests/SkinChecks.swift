precondition(FibuSkin.allCases.count == 12)
precondition(Set(FibuSkin.allCases.map(\.rawValue)).count == FibuSkin.allCases.count)
precondition(FibuSkin.saved("unknown-future-skin") == .original)
precondition(FibuSkin.original.textureName == nil)
let items = FibuSkin.allCases.map { skin -> [String: String] in
    precondition(FibuSkin.saved(skin.rawValue) == skin)
    return ["id": skin.id, "texture": skin.textureName ?? "", "icon": skin.iconName]
}
let json = try JSONSerialization.data(withJSONObject: items)
print(String(data: json, encoding: .utf8)!)
