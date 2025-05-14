document.addEventListener('DOMContentLoaded', function() {
    var popup = document.getElementById('submit-query-popup');
    if (!popup) {
        console.error("Popup element not found");
        return;
    }
    
    // Remove native draggable attribute if set
    popup.removeAttribute('draggable');

    var isDragging = false;
    var offset = { x: 0, y: 0 };

    popup.addEventListener('mousedown', function(e) {
        console.log("mousedown event", e);
        isDragging = true;
        // Calculate the offset between the mouse position and the popup's top-left corner.
        offset.x = e.clientX - popup.offsetLeft;
        offset.y = e.clientY - popup.offsetTop;
        // Prevent text selection while dragging.
        e.preventDefault();
    });

    document.addEventListener('mouseup', function(e) {
        console.log("mouseup event", e);
        isDragging = false;
    });

    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        console.log("mousemove event", e);
        // Update the popup's position based on the mouse movement.
        popup.style.left = (e.clientX - offset.x) + "px";
        popup.style.top = (e.clientY - offset.y) + "px";
        // Remove the transform so it won't interfere.
        popup.style.transform = "none";
    });
});