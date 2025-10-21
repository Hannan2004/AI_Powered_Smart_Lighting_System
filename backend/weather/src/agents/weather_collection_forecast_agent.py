import logging
import requests
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain.schema import HumanMessage
from langgraph import StateGraph, END
from typing_extensions import TypedDict
from ..config.settings import config
from ..kafka.kafka_producer import weather_producer

logger = logging.getLogger(__name__)

class WeatherCollectionState(TypedDict):
    """State class for weather collection and forecast workflow"""
    zones_to_process: List[str]
    current_weather: Dict[str, Any]
    forecast_data: Dict[str, Any]
    api_responses: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    processed_zones: List[str]
    ml_predictions: Dict[str, Any]
    alerts_generated: List[Dict[str, Any]]
    errors: List[str]
    status: str

class WeatherCollectionForecastAgent:
    """
    LangGraph-based agent for collecting weather data and generating forecasts
    using OpenWeather API and ML-based predictions
    """
    
    def __init__(self):
        self.openweather_config = config.get_openweather_config()
        self.groq_config = config.get_groq_config()
        self.llm = ChatGroq(
            groq_api_key=self.groq_config['api_key'],
            model_name=self.groq_config['model'],
            temperature=self.groq_config['temperature'],
            max_tokens=self.groq_config['max_tokens']
        )
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow for weather collection"""
        workflow = StateGraph(WeatherCollectionState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_collection)
        workflow.add_node("fetch_current_weather", self._fetch_current_weather_node)
        workflow.add_node("fetch_forecasts", self._fetch_forecasts_node)
        workflow.add_node("calculate_confidence", self._calculate_confidence_node)
        workflow.add_node("generate_ml_predictions", self._generate_ml_predictions_node)
        workflow.add_node("generate_alerts", self._generate_alerts_node)
        workflow.add_node("publish_data", self._publish_data_node)
        workflow.add_node("finalize", self._finalize_collection)
        
        # Define workflow edges
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "fetch_current_weather")
        workflow.add_edge("fetch_current_weather", "fetch_forecasts")
        workflow.add_edge("fetch_forecasts", "calculate_confidence")
        workflow.add_edge("calculate_confidence", "generate_ml_predictions")
        workflow.add_edge("generate_ml_predictions", "generate_alerts")
        workflow.add_edge("generate_alerts", "publish_data")
        workflow.add_edge("publish_data", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def collect_weather_data(self) -> Dict[str, Any]:
        """Main method to execute weather collection workflow"""
        try:
            logger.info("Starting weather data collection workflow")
            
            # Initialize state
            initial_state = WeatherCollectionState(
                zones_to_process=config.DEFAULT_ZONES.copy(),
                current_weather={},
                forecast_data={},
                api_responses=[],
                confidence_scores={},
                processed_zones=[],
                ml_predictions={},
                alerts_generated=[],
                errors=[],
                status="initializing"
            )
            
            # Execute workflow
            final_state = self.workflow.invoke(initial_state)
            
            return {
                "status": final_state["status"],
                "processed_zones": len(final_state["processed_zones"]),
                "total_zones": len(config.DEFAULT_ZONES),
                "average_confidence": (
                    sum(final_state["confidence_scores"].values()) / 
                    len(final_state["confidence_scores"]) 
                    if final_state["confidence_scores"] else 0
                ),
                "ml_predictions": final_state["ml_predictions"],
                "alerts_generated": len(final_state["alerts_generated"]),
                "errors": final_state["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in weather collection workflow: {e}")
            return {
                "status": "workflow_failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _initialize_collection(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Initialize weather data collection"""
        logger.info("Initializing weather data collection")
        
        state["status"] = "collecting_data"
        state["zones_to_process"] = config.DEFAULT_ZONES.copy()
        
        return state
    
    def _fetch_current_weather_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Fetch current weather data for all zones"""
        logger.info("Fetching current weather data")
        
        for zone_id in state["zones_to_process"]:
            try:
                zone_config = config.get_zone_config(zone_id)
                current_weather = self._fetch_current_weather(zone_config)
                
                if current_weather:
                    state["current_weather"][zone_id] = current_weather
                    state["api_responses"].append({
                        "zone_id": zone_id,
                        "type": "current_weather",
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    state["errors"].append(f"Failed to fetch current weather for {zone_id}")
                    
            except Exception as e:
                error_msg = f"Error fetching current weather for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _fetch_forecasts_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Fetch forecast data for all zones"""
        logger.info("Fetching forecast data")
        
        for zone_id in state["zones_to_process"]:
            try:
                zone_config = config.get_zone_config(zone_id)
                forecast_data = self._fetch_forecast_data(zone_config)
                
                if forecast_data:
                    state["forecast_data"][zone_id] = forecast_data
                    state["api_responses"].append({
                        "zone_id": zone_id,
                        "type": "forecast_data",
                        "success": True,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    state["errors"].append(f"Failed to fetch forecast for {zone_id}")
                    
            except Exception as e:
                error_msg = f"Error fetching forecast for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _calculate_confidence_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Calculate confidence scores for all zones"""
        logger.info("Calculating confidence scores")
        
        for zone_id in state["zones_to_process"]:
            try:
                current_weather = state["current_weather"].get(zone_id)
                forecast_data = state["forecast_data"].get(zone_id)
                
                confidence = self._calculate_confidence_score(current_weather, forecast_data)
                state["confidence_scores"][zone_id] = confidence
                
                if current_weather or forecast_data:
                    state["processed_zones"].append(zone_id)
                    
            except Exception as e:
                error_msg = f"Error calculating confidence for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _generate_ml_predictions_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Generate ML-enhanced predictions using LLM"""
        logger.info("Generating ML-enhanced predictions")
        
        try:
            # Prepare weather summary
            weather_summary = self._prepare_weather_summary(state)
            
            prompt = f"""
            Analyze the following weather data and provide enhanced predictions for smart lighting system:
            
            Weather Data Summary:
            {weather_summary}
            
            Provide analysis for:
            1. Short-term predictions (next 6 hours) for each zone
            2. Lighting impact assessment (visibility, safety concerns)
            3. Risk level assessment (low, medium, high, critical)
            4. Recommended lighting adjustments
            5. Confidence level for predictions (0-100%)
            
            Focus on conditions affecting outdoor lighting: fog, storms, visibility, precipitation.
            Respond in structured format.
            """
            
            message = HumanMessage(content=prompt)
            response = self.llm.invoke([message])
            
            state["ml_predictions"] = {
                "analysis": response.content,
                "generated_at": datetime.now().isoformat(),
                "zones_analyzed": len(state["processed_zones"]),
                "confidence": "ml_enhanced"
            }
            
        except Exception as e:
            error_msg = f"Error in ML prediction generation: {str(e)}"
            logger.error(error_msg)
            state["errors"].append(error_msg)
            state["ml_predictions"] = {"error": error_msg}
        
        return state
    
    def _generate_alerts_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Generate weather alerts based on conditions"""
        logger.info("Generating weather alerts")
        
        for zone_id in state["processed_zones"]:
            try:
                current_weather = state["current_weather"].get(zone_id)
                
                if current_weather and self._requires_weather_alert(current_weather):
                    alert_type, severity = self._determine_alert_details(current_weather)
                    
                    alert = {
                        "zone_id": zone_id,
                        "alert_type": alert_type,
                        "severity": severity,
                        "conditions": current_weather,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    state["alerts_generated"].append(alert)
                    
            except Exception as e:
                error_msg = f"Error generating alert for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        return state
    
    def _publish_data_node(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Publish collected data to Kafka"""
        logger.info("Publishing weather data to Kafka")
        
        published_count = 0
        
        for zone_id in state["processed_zones"]:
            try:
                current_weather = state["current_weather"].get(zone_id)
                forecast_data = state["forecast_data"].get(zone_id)
                confidence = state["confidence_scores"].get(zone_id, 0.5)
                
                # Publish current weather
                if current_weather:
                    weather_producer.publish_sensor_data(zone_id, current_weather)
                    published_count += 1
                
                # Publish forecast
                if forecast_data:
                    weather_producer.publish_weather_forecast(zone_id, forecast_data, confidence)
                    published_count += 1
                
            except Exception as e:
                error_msg = f"Error publishing data for {zone_id}: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        # Publish alerts
        for alert in state["alerts_generated"]:
            try:
                weather_producer.publish_weather_alert(
                    alert["zone_id"],
                    alert["alert_type"],
                    alert["severity"],
                    alert["conditions"]
                )
                published_count += 1
                
            except Exception as e:
                error_msg = f"Error publishing alert: {str(e)}"
                logger.error(error_msg)
                state["errors"].append(error_msg)
        
        logger.info(f"Published {published_count} weather data items to Kafka")
        return state
    
    def _finalize_collection(self, state: WeatherCollectionState) -> WeatherCollectionState:
        """Finalize weather data collection workflow"""
        logger.info("Finalizing weather data collection")
        
        if len(state["processed_zones"]) > 0:
            state["status"] = "collection_complete"
        else:
            state["status"] = "collection_failed"
        
        return state
    
    # Helper methods (same as before but adapted for LangGraph)
    def _fetch_current_weather(self, zone_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch current weather data from OpenWeather API"""
        try:
            coordinates = zone_config['coordinates']
            url = f"{self.openweather_config['base_url']}/weather"
            
            params = {
                'lat': coordinates['lat'],
                'lon': coordinates['lon'],
                'appid': self.openweather_config['api_key'],
                'units': self.openweather_config['units']
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'wind_direction': data['wind'].get('deg', 0),
                'visibility': data.get('visibility', 10000),
                'weather_condition': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'cloudiness': data['clouds']['all'],
                'precipitation': data.get('rain', {}).get('1h', 0) + data.get('snow', {}).get('1h', 0),
                'timestamp': datetime.now().isoformat(),
                'source': 'openweather_current'
            }
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {e}")
            return None
    
    def _fetch_forecast_data(self, zone_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Fetch forecast data from OpenWeather API"""
        try:
            coordinates = zone_config['coordinates']
            url = f"{self.openweather_config['forecast_url']}"
            
            params = {
                'lat': coordinates['lat'],
                'lon': coordinates['lon'],
                'appid': self.openweather_config['api_key'],
                'units': self.openweather_config['units'],
                'cnt': min(config.FORECAST_HOURS // 3, 40)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast_periods = []
            for item in data['list']:
                period = {
                    'datetime': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind']['speed'],
                    'weather_condition': item['weather'][0]['main'],
                    'precipitation': item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0),
                    'precipitation_probability': item.get('pop', 0) * 100
                }
                forecast_periods.append(period)
            
            return {
                'city': data['city']['name'],
                'forecast_periods': forecast_periods,
                'forecast_hours': len(forecast_periods) * 3,
                'timestamp': datetime.now().isoformat(),
                'source': 'openweather_forecast'
            }
            
        except Exception as e:
            logger.error(f"Error fetching forecast data: {e}")
            return None
    
    def _calculate_confidence_score(self, current_weather: Optional[Dict[str, Any]], 
                                  forecast_data: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score for weather predictions"""
        base_confidence = 0.5
        
        if current_weather:
            base_confidence += 0.2
            if current_weather.get('weather_condition') in ['Clear', 'Clouds']:
                base_confidence += 0.1
        
        if forecast_data:
            base_confidence += 0.2
            periods = forecast_data.get('forecast_periods', [])
            if len(periods) >= 8:
                base_confidence += 0.1
        
        return min(max(base_confidence, 0.0), 1.0)
    
    def _prepare_weather_summary(self, state: WeatherCollectionState) -> str:
        """Prepare weather data summary for LLM analysis"""
        summary_parts = []
        
        for zone_id in state["processed_zones"]:
            current = state["current_weather"].get(zone_id, {})
            confidence = state["confidence_scores"].get(zone_id, 0.5)
            
            zone_summary = f"""
            Zone {zone_id}:
            - Current: {current.get('weather_condition', 'Unknown')} ({current.get('temperature', 'N/A')}°C)
            - Visibility: {current.get('visibility', 'Unknown')}m
            - Wind: {current.get('wind_speed', 'Unknown')}m/s
            - Precipitation: {current.get('precipitation', 0)}mm/h
            - Confidence: {confidence:.2f}
            """
            summary_parts.append(zone_summary)
        
        return "\n".join(summary_parts)
    
    def _requires_weather_alert(self, weather_data: Dict[str, Any]) -> bool:
        """Check if current weather conditions require an alert"""
        visibility = weather_data.get('visibility', 10000)
        wind_speed = weather_data.get('wind_speed', 0)
        precipitation = weather_data.get('precipitation', 0)
        condition = weather_data.get('weather_condition', '')
        
        return (
            visibility < config.VISIBILITY_THRESHOLD or
            wind_speed > config.WIND_SPEED_THRESHOLD or
            precipitation > config.PRECIPITATION_THRESHOLD or
            condition in ['Thunderstorm', 'Tornado', 'Fog']
        )
    
    def _determine_alert_details(self, weather_data: Dict[str, Any]) -> tuple:
        """Determine alert type and severity based on conditions"""
        visibility = weather_data.get('visibility', 10000)
        wind_speed = weather_data.get('wind_speed', 0)
        precipitation = weather_data.get('precipitation', 0)
        condition = weather_data.get('weather_condition', '')
        
        # Determine alert type
        if visibility < config.VISIBILITY_THRESHOLD:
            alert_type = "low_visibility"
        elif condition == 'Fog':
            alert_type = "fog"
        elif condition in ['Thunderstorm', 'Tornado']:
            alert_type = "storm"
        else:
            alert_type = "weather_change"
        
        # Determine severity
        if (wind_speed > config.EMERGENCY_WIND_SPEED or 
            precipitation > config.EMERGENCY_PRECIPITATION):
            severity = "critical"
        elif visibility < config.VISIBILITY_THRESHOLD / 2:
            severity = "high"
        else:
            severity = "medium"
        
        return alert_type, severity

# Create agent instance
weather_collection_forecast_agent = WeatherCollectionForecastAgent()