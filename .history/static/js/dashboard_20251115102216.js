
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

    // Fonction pour charger les métriques de performance
    function loadPerformanceMetrics() {
        // Charger les métriques de performance via l'API FastAPI
        fetch('/api/v2/performance/')
            .then(response => response.json())
            .then(metrics => {
                // Mettre à jour les statistiques de performance
                if (metrics && metrics.length > 0) {
                    // Calculer le temps moyen d'envoi
                    const totalDuration = metrics.reduce((sum, metric) => sum + metric.duration, 0);
                    const avgDuration = totalDuration / metrics.length;
                    document.getElementById('avg-performance').textContent = avgDuration.toFixed(4) + 's';
                    
                    // Mettre à jour le nombre total de métriques
                    document.getElementById('total-performance').textContent = metrics.length;
                    
                    // Mettre à jour la date de la dernière métrique
                    const latestMetric = metrics[0];
                    document.getElementById('latest-performance').textContent = 
                        new Date(latestMetric.timestamp).toLocaleTimeString('fr-FR');
                    
                    // Mettre à jour la table des métriques
                    const performanceTable = document.getElementById('performance-table');
                    performanceTable.innerHTML = '';
                    
                    // Limiter à 5 dernières métriques pour ne pas surcharger l'interface
                    const recentMetrics = metrics.slice(0, 5);
                    recentMetrics.forEach(metric => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${metric.method_name}</td>
                            <td>${metric.duration.toFixed(4)}s</td>
                            <td>${new Date(metric.timestamp).toLocaleString('fr-FR')}</td>
                        `;
                        performanceTable.appendChild(row);
                    });
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement des métriques de performance:', error);
                // Mettre à jour la table pour indiquer qu'il y a eu une erreur
                const performanceTable = document.getElementById('performance-table');
                performanceTable.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center text-danger">
                            Erreur de chargement des métriques de performance
