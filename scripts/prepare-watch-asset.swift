import SceneKit
import AppKit
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let scene = try SCNScene(url: root.appendingPathComponent("Assets/Models/Fibu.Soft.usdz"))
func firstFrame(_ animation: CAAnimation, root: SCNNode) {
 if let group = animation as? CAAnimationGroup {
  for child in group.animations ?? [] { firstFrame(child, root: root) }
 } else if let channel = animation as? CAKeyframeAnimation,
           let path = channel.keyPath, let value = channel.values?.first as? NSValue {
  let parts = path.split(separator: ".")
  let node = parts.count == 2 ? root.childNode(withName: String(parts[0].dropFirst()), recursively: true) : root
  switch parts.last {
  case "position": node?.position = value.scnVector3Value
  case "orientation": node?.orientation = value.scnVector4Value
  case "scale": node?.scale = value.scnVector3Value
  case "eulerAngles": node?.eulerAngles = value.scnVector3Value
  default: break
  }
 }
}
scene.rootNode.enumerateChildNodes { node, _ in
 for key in node.animationKeys {
  if let player = node.animationPlayer(forKey: key) {
   firstFrame(CAAnimation(scnAnimation: player.animation), root: node)
   player.paused = true
  }
 }
}
let result = scene.write(to: root.appendingPathComponent("Assets/Models/Fibu.Watch.scn"), options: nil, delegate: nil, progressHandler: nil)
precondition(result)
print("Exported Watch scene with first-frame rest pose and original wave clips")

let reloaded = try SCNScene(url: root.appendingPathComponent("Assets/Models/Fibu.Watch.scn"))
var clips = 0
var bones = 0
reloaded.rootNode.enumerateChildNodes { node, _ in
    clips += node.animationKeys.count
    if let skinner = node.skinner { bones = max(bones, skinner.bones.count) }
}
precondition(clips == 2 && bones == 32, "Watch export must preserve both clips and all 32 bones")
print("PASS: Watch asset reloads with 32 bones and both animation groups")
