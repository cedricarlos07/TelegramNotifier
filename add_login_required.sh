#!/bin/bash

# Fichier cible
FILE="routes.py"

# Liste des routes à protéger
ROUTES=(
    "@app.route('/courses/edit/<int:course_id>', methods=['POST'])"
    "@app.route('/courses/delete/<int:course_id>', methods=['POST'])"
    "@app.route('/zoom-links')"
    "@app.route('/zoom-links/update/<int:course_id>', methods=['POST'])"
    "@app.route('/scenarios')"
    "@app.route('/scenarios/run/<scenario_name>', methods=['POST'])"
    "@app.route('/logs')"
    "@app.route('/api/send-test-message', methods=['POST'])"
    "@app.route('/api/export-excel', methods=['POST'])"
    "@app.route('/simulation')"
    "@app.route('/simulation/toggle', methods=['POST'])"
    "@app.route('/bot-status')"
    "@app.route('/check-group', methods=['POST'])"
    "@app.route('/rankings')"
    "@app.route('/create-demo-course', methods=['POST'])"
    "@app.route('/import-demo-excel', methods=['POST'])"
    "@app.route('/send-demo-notification', methods=['POST'])"
    "@app.route('/send-demo-course/<int:course_id>', methods=['POST'])"
    "@app.route('/delete-demo-course/<int:course_id>', methods=['POST'])"
    "@app.route('/send-rankings', methods=['POST'])"
)

# Pour chaque route à protéger
for route in "${ROUTES[@]}"; do
    # Échapper les caractères spéciaux pour sed
    escaped_route=$(echo "$route" | sed -e 's/[\/&]/\\&/g')
    
    # Vérifier si le décorateur est déjà présent
    if ! grep -A 1 "$escaped_route" "$FILE" | grep -q "@login_required"; then
        # Ajouter le décorateur login_required
        sed -i "s/$escaped_route/&\n    @login_required/" "$FILE"
        echo "Ajout de @login_required à $route"
    else
        echo "Décorateur déjà présent pour $route"
    fi
done

echo "Opération terminée!"
