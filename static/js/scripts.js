document.addEventListener("DOMContentLoaded", function() {
    const hasChildrenField = document.querySelector("#id_has_children");
    const numberOfChildrenField = document.querySelector("#id_number_of_children").parentElement;

    function toggleNumberOfChildren() {
        if (hasChildrenField.checked) {
            numberOfChildrenField.style.display = "block";
        } else {
            numberOfChildrenField.style.display = "none";
        }
    }

    hasChildrenField.addEventListener("change", toggleNumberOfChildren);
    toggleNumberOfChildren();  // Call once on page load to ensure correct state
});
