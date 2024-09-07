document.addEventListener('DOMContentLoaded', function () {
    const hasChildrenCheckbox = document.querySelector('#id_has_children');
    const numberOfChildrenField = document.querySelector('#id_number_of_children');

    function toggleChildrenField() {
        if (hasChildrenCheckbox.checked) {
            numberOfChildrenField.disabled = false;
        } else {
            numberOfChildrenField.disabled = true;
            numberOfChildrenField.value = '';
        }
    }

    hasChildrenCheckbox.addEventListener('change', toggleChildrenField);
    toggleChildrenField();  // Set initial state based on current value
});