import QtQuick

Item {
    property string label: "salamah"
    property alias textColor: text.color

    Text {
        id: text
        x: 12
        anchors.verticalCenter: parent.verticalCenter
        text: parent.label
        color: "#e7edf0"
        font.family: "JetBrains Mono"
        font.pixelSize: 14
    }
}
