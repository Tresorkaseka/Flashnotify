
// Script pour le rafraîchissement en temps réel du dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour charger les données de statistiques
    function loadStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                // Mettre à jour les statistiques générales
                document.querySelector('.bg-primary .card-body h2').textContent = data.total_notifications;
