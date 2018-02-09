function(modal) {
    modal.respond('formChosen', {{ form_json|safe }});
    modal.close();
}
