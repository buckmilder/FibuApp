import SwiftUI

struct SkinPicker: View {
    @Binding var selectedID: String
    @Environment(\.dismiss) private var dismiss
    private let ink = Color(red: 0.14, green: 0.28, blue: 0.23)

    var body: some View {
        VStack(spacing: 0) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Fibudex").font(.system(.title2, design: .rounded, weight: .bold))
                    Text("Choose Fibu’s skin.").font(.subheadline).foregroundStyle(.secondary)
                }
                Spacer()
                Button("Done") { dismiss() }.font(.subheadline.weight(.semibold))
                    .padding(.vertical, 6)
            }.padding(22)
            ScrollView {
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 90), spacing: 12)], spacing: 12) {
                    ForEach(FibuSkin.allCases) { skin in
                        let selected = FibuSkin.saved(selectedID) == skin
                        Button { selectedID = skin.rawValue } label: {
                            VStack(spacing: 5) {
                                Image(skin.iconName).renderingMode(.original).resizable().aspectRatio(contentMode: .fit)
                                    .frame(height: 72).padding(.top, 12)
                                    .accessibilityHidden(true)
                                Text(skin.name).font(.system(.caption, design: .rounded, weight: .semibold))
                                    .padding(.bottom, 10)
                            }
                            .frame(maxWidth: .infinity)
                            .background(Color(red: 0.90, green: 0.95, blue: 0.89), in: RoundedRectangle(cornerRadius: 18))
                            .clipShape(RoundedRectangle(cornerRadius: 18))
                            .overlay(RoundedRectangle(cornerRadius: 18).stroke(selected ? ink : .clear, lineWidth: 2))
                            .overlay(alignment: .topTrailing) {
                                if selected {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(.white, ink).padding(7)
                                }
                            }
                        }.buttonStyle(.plain)
                            .accessibilityLabel(skin.name + " skin")
                            .accessibilityAddTraits(selected ? .isSelected : [])
                    }
                }.padding(.horizontal, 22).padding(.bottom, 24)
            }
        }
        .foregroundStyle(ink)
        .background(Color(red: 0.97, green: 0.98, blue: 0.95))
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }
}
