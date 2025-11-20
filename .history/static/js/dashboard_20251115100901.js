// Script pour le rafraîchissement en temps réel du dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Fonction pour charger les données de statistiques
    function loadStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                // Mettre à jour les statistiques générales
                document.querySelector('.bg-primary .card-body h2').textContent = data.total_notifications;
                document.querySelector('.bg-danger .card-body h2').textContent = data.by_priority.CRITICAL || 0;
                document.querySelector('.bg-warning .card-body h2').textContent = data.by_priority.HIGH || 0;
                document.querySelector('.bg-success .card-body h2').textContent = 
                    (data.by_priority.MEDIUM || 0) + (data.by_priority.LOW || 0);

                // Mettre à jour les statistiques par type
                const typeStats = document.querySelectorAll('.col-md-4.mb-2');
                typeStats.forEach(stat => {
                    const typeSpan = stat.querySelector('span');
                    const type = typeSpan.textContent.trim().toLowerCase();
                    const countBadge = stat.querySelector('.badge');
                    if (data.by_type && data.by_type[type]) {
                        countBadge.textContent = data.by_type[type];
                    }
                });
            })
            .catch(error => console.error('Erreur lors du chargement des stats:', error));
    }

    // Fonction pour charger les notifications
    function loadNotifications() {
        fetch('/api/notifications')
            .then(response => response.json())
            .then(notifications => {
                // Mettre à jour la table des notifications
                const tbody = document.querySelector('table tbody');
                if (tbody) {
                    // Effacer les anciennes notifications
                    tbody.innerHTML = '';
                    
                    // Ajouter les nouvelles notifications
                    notifications.forEach(notif => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${new Date(notif.created_at).toLocaleString('fr-FR')}</td>
                            <td>${notif.user_name}</td>
                            <td>
                                <strong>${notif.title}</strong><br>
                                <small class="text-muted">${notif.body.substring(0, 50)}...</small>
                            </td>
                            <td>
                                <span class="badge bg-info">${notif.emergency_type}</span>
                            </td>
                            <td>
                                <span class="badge ${getPriorityClass(notif.priority)}">
                                    ${notif.priority}
                                </span>
                            </td>
                            <td>${notif.channels || 'N/A'}</td>
                        `;
                        tbody.appendChild(row);
                    });
                    
                    // Afficher un message s'il n'y a pas de notifications
                    if (notifications.length === 0) {
                        tbody.innerHTML = `
                            <tr>
                                <td colspan="6" class="text-center">
                                    <div class="alert alert-info">Aucune notification trouvée. <a href="/send">Envoyez votre première notification</a></div>
                                </td>
                            </tr>
                        `;
                    }
                }
            })
            .catch(error => console.error('Erreur lors du chargement des notifications:', error));
    }

    // Fonction pour déterminer la classe CSS selon la priorité
    function getPriorityClass(priority) {
        switch(priority) {
            case 'CRITICAL': return 'bg-danger';
            case 'HIGH': return 'bg-warning text-dark';
            default: return 'bg-success';
        }
    }

    // Rafraîchir les données toutes les 30 secondes
    loadStats();
    loadNotifications();
    
    setInterval(() => {
        loadStats();
        loadNotifications();
    }, 30000); // 30 secondes
    
    // Rafraîchir immédiatement quand l'utilisateur clique sur le bouton de rafraîchissement
    const refreshButton = document.createElement('button');
    refreshButton.className = 'btn btn-sm btn-outline-secondary ms-2';
    refreshButton.innerHTML = '🔄';
    refreshButton.title = 'Rafraîchir';
    refreshButton.onclick = function() {
        loadStats();
        loadNotifications();
    };
    
    // Ajouter le bouton de rafraîchissement à la barre de navigation
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        const refreshContainer = document.createElement('div');
        refreshContainer.className = 'd-flex align-items-center';
        refreshContainer.appendChild(refreshButton);
        navbar.querySelector('.ms-auto').prepend(refreshContainer);
    }
});