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
        // Charger les métriques de performance via l'API Flask
        fetch('/api/performance')
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
                        </td>
                    </tr>
                `;
            });
    }

    // Fonction pour charger le statut de la file d'attente
    function loadQueueStatus() {
        fetch('/api/queue/status')
            .then(response => response.json())
            .then(data => {
                // Mettre à jour les statistiques de la file d'attente
                document.getElementById('queue-size').textContent = data.queue_size;
                document.getElementById('running-tasks').textContent = data.running_tasks;
                document.getElementById('pending-tasks').textContent = data.pending_tasks;
                document.getElementById('total-tasks').textContent = data.total_tasks;
                
                // Mettre à jour la table des tâches
                const queueTable = document.getElementById('queue-table');
                queueTable.innerHTML = '';
                
                if (data.tasks && data.tasks.length > 0) {
                    data.tasks.forEach(task => {
                        const row = document.createElement('tr');
                        const statusClass = getStatusClass(task.status);
                        const errorText = task.error ? `<br><small class="text-danger">${task.error}</small>` : '';
                        
                        row.innerHTML = `
                            <td><code>${task.id.substring(0, 8)}...</code></td>
                            <td><span class="badge ${statusClass}">${task.status}</span></td>
                            <td>${new Date(task.created_at).toLocaleString('fr-FR')}</td>
                            <td>${task.priority}</td>
                            <td>${task.retry_count}/3</td>
                            <td>${errorText}</td>
                        `;
                        queueTable.appendChild(row);
                    });
                } else {
                    queueTable.innerHTML = `
                        <tr>
                            <td colspan="6" class="text-center">Aucune tâche dans la file d'attente</td>
                        </tr>
                    `;
                }
                
                // Mettre à jour la section des notifications récentes
                const recentNotificationsTable = document.getElementById('recent-notifications-table');
                if (recentNotificationsTable) {
                    recentNotificationsTable.innerHTML = '';
                    
                    if (data.recent_notifications && data.recent_notifications.length > 0) {
                        data.recent_notifications.forEach(notif => {
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
                            recentNotificationsTable.appendChild(row);
                        });
                    } else {
                        recentNotificationsTable.innerHTML = `
                            <tr>
                                <td colspan="6" class="text-center">Aucune notification récente</td>
                            </tr>
                        `;
                    }
                }
            })
            .catch(error => {
                console.error('Erreur lors du chargement du statut de la file d\'attente:', error);
                const queueTable = document.getElementById('queue-table');
                queueTable.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-danger">
                            Erreur de chargement de la file d'attente
                        </td>
                    </tr>
                `;
            });
    }

    // Fonction pour effacer la file d'attente
    function clearQueue() {
        if (confirm('Êtes-vous sûr de vouloir effacer la file d\'attente ?')) {
            fetch('/api/queue/clear', {
                method: 'POST'
            })
            .then(response => {
                if (response.ok) {
                    alert('File d\'attente effacée avec succès');
                    loadQueueStatus();
                } else {
                    alert('Erreur lors de l\'effacement de la file d\'attente');
                }
            })
            .catch(error => {
                console.error('Erreur lors de l\'effacement de la file d\'attente:', error);
                alert('Erreur lors de l\'effacement de la file d\'attente');
            });
        }
    }

    // Fonction pour déterminer la classe CSS selon le statut
    function getStatusClass(status) {
        switch(status) {
            case 'running': return 'bg-success';
            case 'pending': return 'bg-warning';
            case 'completed': return 'bg-info';
            case 'failed': return 'bg-danger';
            case 'retrying': return 'bg-secondary';
            default: return 'bg-secondary';
        }
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
    loadPerformanceMetrics();
    loadQueueStatus();
    
    setInterval(() => {
        loadStats();
        loadNotifications();
        loadPerformanceMetrics();
        loadQueueStatus();
    }, 30000); // 30 secondes
    
    // Rafraîchir immédiatement quand l'utilisateur clique sur le bouton de rafraîchissement
    const refreshButton = document.createElement('button');
    refreshButton.className = 'btn btn-sm btn-outline-secondary ms-2';
    refreshButton.innerHTML = '🔄';
    refreshButton.title = 'Rafraîchir';
    refreshButton.onclick = function() {
        loadStats();
        loadNotifications();
        loadPerformanceMetrics();
        loadQueueStatus();
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