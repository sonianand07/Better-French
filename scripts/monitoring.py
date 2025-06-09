#!/usr/bin/env python3
"""
Better French Max - System Monitor
Enterprise-grade monitoring for automated system
Tracks health, performance, quality metrics, and costs
"""

import os
import sys
import json
import time
import psutil
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
import threading

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))
from automation import AUTOMATION_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    Enterprise-grade system monitoring for Better French Max automation
    Tracks performance, quality, costs, and system health
    """
    
    def __init__(self):
        self.monitoring_config = AUTOMATION_CONFIG['monitoring']
        self.reliability_config = AUTOMATION_CONFIG['reliability']
        self.cost_config = AUTOMATION_CONFIG['cost']
        
        # Monitoring state
        self.metrics = {
            'system_health': {},
            'performance': {},
            'quality': {},
            'costs': {},
            'alerts': []
        }
        
        # Paths
        self.logs_dir = os.path.join(os.path.dirname(__file__), '..', 'logs')
        self.data_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'live')
        self.metrics_file = os.path.join(self.logs_dir, 'metrics.json')
        
        # Ensure directories exist
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Start time for uptime tracking
        self.start_time = datetime.now(timezone.utc)
        
        # Threading for background monitoring
        self.monitoring_active = False
        self.monitor_thread = None
        
        logger.info("📊 System Monitor initialized")
        logger.info(f"🔍 Health check interval: {self.reliability_config['health_check_interval']} minutes")
    
    def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        health_status = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'issues': [],
            'metrics': {}
        }
        
        try:
            # 1. System Resource Health
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_status['metrics']['system'] = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'disk_percent': disk.percent,
                'uptime_hours': (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600
            }
            
            # Check system resource alerts
            if memory.percent > self.reliability_config['memory_usage_limit']:
                health_status['issues'].append(f"High memory usage: {memory.percent:.1f}%")
                health_status['status'] = 'warning'
            
            if cpu_percent > 90:
                health_status['issues'].append(f"High CPU usage: {cpu_percent:.1f}%")
                health_status['status'] = 'warning'
            
            if disk.percent > 90:
                health_status['issues'].append(f"High disk usage: {disk.percent:.1f}%")
                health_status['status'] = 'warning'
            
            # 2. Component Health
            component_health = self._check_component_health()
            health_status['metrics']['components'] = component_health
            
            if not component_health.get('all_operational', True):
                health_status['issues'].append("Some components not operational")
                health_status['status'] = 'warning'
            
            # 3. Data Freshness
            data_health = self._check_data_freshness()
            health_status['metrics']['data'] = data_health
            
            if not data_health.get('data_fresh', True):
                health_status['issues'].append(f"Stale data detected: {data_health.get('hours_since_update', 'unknown')} hours")
                health_status['status'] = 'warning'
            
            # 4. Quality Trends
            quality_health = self._check_quality_trends()
            health_status['metrics']['quality'] = quality_health
            
            if quality_health.get('declining_quality', False):
                health_status['issues'].append("Quality decline detected")
                health_status['status'] = 'warning'
            
            # 5. Cost Monitoring
            cost_health = self._check_cost_status()
            health_status['metrics']['costs'] = cost_health
            
            if cost_health.get('cost_alert', False):
                health_status['issues'].append(f"Cost alert: ${cost_health.get('daily_cost', 0):.2f}")
                health_status['status'] = 'warning'
            
            # Determine overall status
            if len(health_status['issues']) > 3:
                health_status['status'] = 'critical'
            
            # Store metrics
            self.metrics['system_health'] = health_status
            
        except Exception as e:
            health_status['status'] = 'error'
            health_status['issues'].append(f"Health check failed: {e}")
            logger.error(f"❌ Health check error: {e}")
        
        return health_status
    
    def _check_component_health(self) -> Dict[str, Any]:
        """Check health of individual components"""
        components = {
            'smart_scraper': False,
            'quality_curator': False,
            'website_updater': False,
            'ai_processor': False
        }
        
        try:
            # Check if component files exist and are recent
            scripts_dir = os.path.dirname(__file__)
            
            for component in components:
                component_file = os.path.join(scripts_dir, f"{component}.py")
                if os.path.exists(component_file):
                    components[component] = True
            
            return {
                'components': components,
                'all_operational': all(components.values()),
                'operational_count': sum(components.values()),
                'total_components': len(components)
            }
            
        except Exception as e:
            logger.error(f"❌ Component health check failed: {e}")
            return {'error': str(e), 'all_operational': False}
    
    def _check_data_freshness(self) -> Dict[str, Any]:
        """Check if data is fresh and up-to-date"""
        try:
            # Check latest website data
            website_data_file = os.path.join(self.data_dir, 'website_data.json')
            
            if os.path.exists(website_data_file):
                with open(website_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                last_update = data.get('metadata', {}).get('updated_at')
                if last_update:
                    update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                    hours_since_update = (datetime.now(timezone.utc) - update_time).total_seconds() / 3600
                    
                    max_age = self.reliability_config['max_article_age_hours']
                    data_fresh = hours_since_update < max_age
                    
                    return {
                        'data_fresh': data_fresh,
                        'hours_since_update': hours_since_update,
                        'max_age_hours': max_age,
                        'last_update': last_update,
                        'article_count': data.get('metadata', {}).get('total_articles', 0)
                    }
            
            return {
                'data_fresh': False,
                'error': 'No website data found',
                'hours_since_update': float('inf')
            }
            
        except Exception as e:
            logger.error(f"❌ Data freshness check failed: {e}")
            return {'error': str(e), 'data_fresh': False}
    
    def _check_quality_trends(self) -> Dict[str, Any]:
        """Check for quality decline trends"""
        try:
            # Look for recent curated articles to analyze quality trends
            quality_scores = []
            
            # Check today's curated articles
            today = datetime.now(timezone.utc).date().isoformat()
            curated_file = os.path.join(self.data_dir, f"curated_articles_{today}.json")
            
            if os.path.exists(curated_file):
                with open(curated_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                articles = data.get('articles', [])
                if articles:
                    quality_scores = [a.get('total_score', 0) for a in articles]
            
            if quality_scores:
                avg_quality = sum(quality_scores) / len(quality_scores)
                min_quality = min(quality_scores)
                max_quality = max(quality_scores)
                
                # Simple quality decline detection
                threshold = AUTOMATION_CONFIG['quality']['min_total_score']
                below_threshold = len([s for s in quality_scores if s < threshold])
                
                return {
                    'average_quality': avg_quality,
                    'min_quality': min_quality,
                    'max_quality': max_quality,
                    'total_articles': len(quality_scores),
                    'below_threshold': below_threshold,
                    'declining_quality': below_threshold > len(quality_scores) * 0.3,  # 30% threshold
                    'quality_threshold': threshold
                }
            
            return {
                'average_quality': 0,
                'declining_quality': False,
                'error': 'No quality data available'
            }
            
        except Exception as e:
            logger.error(f"❌ Quality trends check failed: {e}")
            return {'error': str(e), 'declining_quality': False}
    
    def _check_cost_status(self) -> Dict[str, Any]:
        """Check current cost status and alerts"""
        try:
            # This would integrate with actual cost tracking
            # For now, simulate cost monitoring based on config limits
            
            daily_limit = self.cost_config['daily_cost_limit']
            alert_threshold = self.cost_config['cost_alert_threshold']
            
            # Placeholder for actual cost tracking
            estimated_daily_cost = 0.0  # Would be calculated from actual usage
            
            return {
                'daily_cost': estimated_daily_cost,
                'daily_limit': daily_limit,
                'alert_threshold': alert_threshold,
                'cost_alert': estimated_daily_cost > alert_threshold,
                'cost_critical': estimated_daily_cost > daily_limit,
                'remaining_budget': max(0, daily_limit - estimated_daily_cost)
            }
            
        except Exception as e:
            logger.error(f"❌ Cost status check failed: {e}")
            return {'error': str(e), 'cost_alert': False}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get detailed performance metrics"""
        try:
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'uptime': {
                    'start_time': self.start_time.isoformat(),
                    'uptime_hours': (datetime.now(timezone.utc) - self.start_time).total_seconds() / 3600,
                    'uptime_days': (datetime.now(timezone.utc) - self.start_time).days
                },
                'system': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory': {
                        'total_gb': psutil.virtual_memory().total / (1024**3),
                        'available_gb': psutil.virtual_memory().available / (1024**3),
                        'percent_used': psutil.virtual_memory().percent
                    },
                    'disk': {
                        'total_gb': psutil.disk_usage('/').total / (1024**3),
                        'free_gb': psutil.disk_usage('/').free / (1024**3),
                        'percent_used': psutil.disk_usage('/').percent
                    }
                },
                'process': {
                    'pid': os.getpid(),
                    'threads': threading.active_count(),
                    'memory_mb': psutil.Process().memory_info().rss / (1024**2)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Performance metrics collection failed: {e}")
            return {'error': str(e)}
    
    def get_quality_summary(self) -> Dict[str, Any]:
        """Get quality metrics summary for dashboard"""
        try:
            # Load latest quality data
            today = datetime.now(timezone.utc).date().isoformat()
            curated_file = os.path.join(self.data_dir, f"curated_articles_{today}.json")
            
            if os.path.exists(curated_file):
                with open(curated_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'total_articles': data.get('count', 0),
                    'quality_stats': data.get('metadata', {}).get('statistics', {}),
                    'threshold': AUTOMATION_CONFIG['quality']['min_total_score'],
                    'status': 'active'
                }
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'no_data',
                'message': 'No recent quality data available'
            }
            
        except Exception as e:
            logger.error(f"❌ Quality summary failed: {e}")
            return {'error': str(e), 'status': 'error'}
    
    def save_metrics(self):
        """Save current metrics to file"""
        try:
            metrics_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'system_health': self.metrics.get('system_health', {}),
                'performance': self.get_performance_metrics(),
                'quality': self.get_quality_summary(),
                'monitoring_config': {
                    'health_check_interval': self.reliability_config['health_check_interval'],
                    'quality_threshold': AUTOMATION_CONFIG['quality']['min_total_score'],
                    'cost_limits': {
                        'daily_limit': self.cost_config['daily_cost_limit'],
                        'alert_threshold': self.cost_config['cost_alert_threshold']
                    }
                }
            }
            
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"📊 Metrics saved to {self.metrics_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save metrics: {e}")
    
    def generate_health_report(self) -> str:
        """Generate human-readable health report"""
        health = self.check_system_health()
        performance = self.get_performance_metrics()
        quality = self.get_quality_summary()
        
        report_lines = [
            "🔍 Better French Max - System Health Report",
            "=" * 50,
            f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"⚡ Status: {health['status'].upper()}",
            ""
        ]
        
        # System metrics
        if 'system' in performance:
            sys_metrics = performance['system']
            report_lines.extend([
                "💻 System Resources:",
                f"   CPU Usage: {sys_metrics.get('cpu_percent', 0):.1f}%",
                f"   Memory Usage: {sys_metrics.get('memory', {}).get('percent_used', 0):.1f}%",
                f"   Disk Usage: {sys_metrics.get('disk', {}).get('percent_used', 0):.1f}%",
                f"   Uptime: {performance.get('uptime', {}).get('uptime_hours', 0):.1f} hours",
                ""
            ])
        
        # Quality metrics
        if quality.get('status') == 'active':
            stats = quality.get('quality_stats', {})
            if stats and 'total' in stats:
                report_lines.extend([
                    "🎯 Quality Metrics:",
                    f"   Articles Today: {quality.get('total_articles', 0)}",
                    f"   Average Score: {stats['total'].get('avg', 0):.1f}/30",
                    f"   Quality Threshold: {quality.get('threshold', 0)}/30",
                    ""
                ])
        
        # Issues
        if health['issues']:
            report_lines.extend([
                "⚠️ Issues Detected:",
                *[f"   • {issue}" for issue in health['issues']],
                ""
            ])
        else:
            report_lines.append("✅ No issues detected")
        
        return "\n".join(report_lines)
    
    def start_background_monitoring(self):
        """Start background monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()
            logger.info("🔄 Background monitoring started")
    
    def stop_background_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ Background monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        interval = self.reliability_config['health_check_interval'] * 60  # Convert to seconds
        
        while self.monitoring_active:
            try:
                self.check_system_health()
                self.save_metrics()
                time.sleep(interval)
            except Exception as e:
                logger.error(f"❌ Monitoring loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

# CLI interface for standalone monitoring
def main():
    """Main function for standalone monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Better French Max - System Monitor')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--health', action='store_true', help='Show health report')
    parser.add_argument('--diagnose', action='store_true', help='Run full diagnostics')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    if args.status:
        health = monitor.check_system_health()
        print(f"System Status: {health['status'].upper()}")
        if health['issues']:
            print("Issues:")
            for issue in health['issues']:
                print(f"  • {issue}")
    
    elif args.health:
        print(monitor.generate_health_report())
    
    elif args.diagnose:
        print("🔍 Running full system diagnostics...")
        health = monitor.check_system_health()
        performance = monitor.get_performance_metrics()
        quality = monitor.get_quality_summary()
        
        print("\n" + monitor.generate_health_report())
        
        print("\n📊 Detailed Metrics:")
        print(f"Performance: {json.dumps(performance, indent=2, default=str)}")
        print(f"Quality: {json.dumps(quality, indent=2, default=str)}")
    
    elif args.monitor:
        print("🔄 Starting continuous monitoring (Ctrl+C to stop)...")
        monitor.start_background_monitoring()
        try:
            while True:
                time.sleep(30)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Monitoring active...")
        except KeyboardInterrupt:
            print("\n⏹️ Stopping monitoring...")
            monitor.stop_background_monitoring()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 