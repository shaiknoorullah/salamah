import QtQuick
import QtTest
import ".."

TestCase {
    name: "BarContent"

    BarContent {
        id: bar
        width: 400
        height: 32
    }

    function test_label() {
        compare(bar.label, "salamah");
    }

    function test_text_colour() {
        compare(bar.textColor.toString(), "#e7edf0");
    }
}
