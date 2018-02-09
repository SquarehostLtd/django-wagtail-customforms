$(document).ready(function(e) {
    $('[name*=field_type]').each(function(i,e) {
        var val = $(this).val();
        if (val == 'blocktext') {
            $(this).closest('.fields').find('.formbuilder-help').hide();
            $(this).closest('.fields').find('.formbuilder-required').hide();
            $(this).closest('.fields').find('.formbuilder-choices').hide();
            $(this).closest('.fields').find('.formbuilder-default').hide();
        }

        $(this).on('change', function(e) {
            var val = $(this).val();
            if (val == 'blocktext') {
                $(this).closest('.fields').find('.formbuilder-help').hide();
                $(this).closest('.fields').find('.formbuilder-required').hide();
                $(this).closest('.fields').find('.formbuilder-choices').hide();
                $(this).closest('.fields').find('.formbuilder-default').hide();
            } else {
                $(this).closest('.fields').find('.formbuilder-help').show();
                $(this).closest('.fields').find('.formbuilder-required').show();
                $(this).closest('.fields').find('.formbuilder-choices').show();
                $(this).closest('.fields').find('.formbuilder-default').show();
            }
        });
    });
});
