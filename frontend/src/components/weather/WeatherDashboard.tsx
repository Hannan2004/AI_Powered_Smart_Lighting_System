'use client';
import React, { useState, useEffect } from 'react';
import { getWeatherSystemStatus, getCurrentWeatherData, getWeatherAlerts } from '@/utils/api';
import Card from '@/components/shared/Card';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const WeatherDashboard: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [currentWeather, setCurrentWeather] = useState<any>(null);
    const [alerts, setAlerts] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const [statusData, weatherData, alertsData] = await Promise.all([
                    getWeatherSystemStatus(),
                    getCurrentWeatherData(),
                    getWeatherAlerts()
                ]);

                if (statusData.error) throw new Error(`Status fetch failed: ${statusData.message}`);
                setStatus(statusData);

                if (weatherData.error) throw new Error(`Weather data fetch failed: ${weatherData.message}`);
                setCurrentWeather(weatherData);

                if (alertsData.error) throw new Error(`Alerts fetch failed: ${alertsData.message}`);
                setAlerts(alertsData.alerts || []); // Assuming alerts are in an 'alerts' array

            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to fetch weather data');
                console.error(err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();

        // Optional: Set up polling or WebSocket connection here for real-time updates
        const intervalId = setInterval(fetchData, 60000); // Refresh every 60 seconds
        return () => clearInterval(intervalId); // Cleanup interval on unmount

    }, []);

    if (isLoading) {
        return <LoadingSpinner />;
    }

    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Weather Agent</h2>

            {error && <Card title="Error" className="bg-red-100 border-red-400 text-red-700 dark:bg-red-900 dark:border-red-700 dark:text-red-200">{error}</Card>}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <Card title="System Status">
                    {status ? <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(status.system_status || status.agent_statuses || status, null, 2)}</pre> : <p>No status data</p>}
                </Card>

                <Card title="Current Conditions Overview">
                   {currentWeather?.success && currentWeather?.current_conditions ? (
                     <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(currentWeather.current_conditions, null, 2)}</pre>
                    ) : currentWeather ? (
                     <pre className="text-xs whitespace-pre-wrap">{JSON.stringify(currentWeather, null, 2)}</pre>
                    ): (
                     <p>No current weather data</p>
                    )}
                </Card>

                 <Card title="Active Alerts">
                    {alerts.length > 0 ? (
                        <ul className='space-y-1 text-sm'>
                            {alerts.slice(0, 5).map((alert: any, index: number) => ( // Show max 5 alerts
                                <li key={alert.alert_id || index} className={`p-1 rounded ${alert.severity === 'critical' || alert.severity === 'high' ? 'bg-red-100 dark:bg-red-900' : 'bg-yellow-100 dark:bg-yellow-900'}`}>
                                    [{alert.severity?.toUpperCase()}] {alert.alert_type} in {alert.zone_id}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-sm text-gray-500 dark:text-gray-400">No active alerts.</p>
                    )}
                 </Card>
            </div>

            {/* Placeholder for more detailed weather per zone */}
            {currentWeather?.weather_data && (
                 <Card title="Weather Data Per Zone">
                    <pre className="text-xs whitespace-pre-wrap max-h-60 overflow-auto">{JSON.stringify(currentWeather.weather_data, null, 2)}</pre>
                 </Card>
            )}

            {/* Add more specific widgets here later */}
            {/* e.g., <CurrentConditionsWidget />, <AlertsWidget /> */}
        </div>
    );
};

export default WeatherDashboard;