"""
Run the web application.
"""

from src.app import app
from src.config import get_config
import os
import json
import time

if __name__ == '__main__':
    config = get_config()
    
    # #region agent log
    log_path = os.path.join('.cursor', 'debug.log')
    print(f"[DEBUG] Log path: {os.path.abspath(log_path)}")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        routes = [r.rule for r in app.url_map.iter_rules() if not r.rule.startswith('/static')]
        print(f"[DEBUG] Routes registered: {routes}")
        print(f"[DEBUG] /map in routes: {'/map' in routes}")
        print(f"[DEBUG] App name: {app.name}, App ID: {id(app)}")
        with open(log_path, 'a') as f:
            f.write(json.dumps({"id":"log_startup_routes","timestamp":int(time.time()*1000),"location":"run_web.py","message":"Checking routes at startup","data":{"routes":routes,"map_exists":"/map" in routes,"total_routes":len(routes),"app_name":app.name,"app_id":id(app),"imported_from":"src.app"},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
    except Exception as e:
        print(f"[DEBUG] Error in startup logging: {e}")
        import traceback
        traceback.print_exc()
        try:
            with open(log_path, 'a') as f:
                f.write(json.dumps({"id":"log_startup_error","timestamp":int(time.time()*1000),"location":"run_web.py","message":"Error checking routes","data":{"error":str(e)},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
        except: pass
    # #endregion
    
    print("="*70)
    print("Geopolitical Risk Intelligence Platform - Web Application")
    print("="*70)
    print(f"\nStarting server at http://{config.api.get('host', '127.0.0.1')}:{config.api.get('port', 5000)}")
    print("\nAvailable routes:")
    web_routes = []
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/static') and not rule.rule.startswith('/api'):
            print(f"  {rule.rule}")
            web_routes.append(rule.rule)
    
    # #region agent log
    try:
        with open(log_path, 'a') as f:
            f.write(json.dumps({"id":"log_printed_routes","timestamp":int(time.time()*1000),"location":"run_web.py","message":"Routes printed to console","data":{"routes":web_routes,"map_in_list":"/map" in web_routes,"app_name":app.name,"app_id":id(app)},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    print("\nPress Ctrl+C to stop the server")
    print("="*70)
    
    # #region agent log
    try:
        with open(log_path, 'a') as f:
            f.write(json.dumps({"id":"log_app_run_start","timestamp":int(time.time()*1000),"location":"run_web.py","message":"Starting Flask app.run","data":{"host":config.api.get('host', '127.0.0.1'),"port":config.api.get('port', 5000),"debug":config.api.get('debug', False),"app_name":app.name,"app_id":id(app)},"runId":"pre-fix","hypothesisId":"A"}) + "\n")
    except: pass
    # #endregion
    
    app.run(
        host=config.api.get('host', '127.0.0.1'),
        port=config.api.get('port', 5000),
        debug=config.api.get('debug', False)
    )
