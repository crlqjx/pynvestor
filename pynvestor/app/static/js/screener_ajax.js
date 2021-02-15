$(document).ready(function() {
    $('form').on('submit', function(event) {
        document.getElementById("screenerResult").innerHTML = '';
        var period_buttons = document.getElementsByName("periodBtn");
        for (var i = 0; i < period_buttons.length; i++) {
            if (period_buttons[i].checked == true) {
                var period_value = period_buttons[i].value;
                }
            }
        var screening_fields = {};
        var screening_inputs = document.getElementsByClassName("form-check");
        for (var i = 0; i < screening_inputs.length; i++) {
            if (screening_inputs[i].getElementsByClassName("form-check-input").fieldName.checked == true) {
                var field_name = screening_inputs[i].getElementsByClassName("form-check-input").fieldName.value;
                var field_limits = [parseFloat(screening_inputs[i].getElementsByClassName("form-control").minValue.value),
                                    parseFloat(screening_inputs[i].getElementsByClassName("form-control").maxValue.value)];
                screening_fields[field_name] = field_limits;
            }
        }
        $.ajax({
            data: JSON.stringify(
                {
                    period: period_value,
                    fields: screening_fields
                }
            ),
            type: 'POST',
            url: '/run_screener',
            contentType: "application/json; charset=UTF-8"
        })
        .done(function(data) {
            var result = JSON.parse(data);
//            $('#screenerResult').text(JSON.stringify(result));
            grid("screenerResult", result)
        });

        event.preventDefault();
    })
})