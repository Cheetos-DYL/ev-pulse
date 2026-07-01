"""Export EV Pulse SQLite database to seed_data.json for Render auto-seed."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

def export_seed(output_path=None):
    if not output_path:
        output_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'app', 'seed_data.json')
    
    from app.db import get_connection
    
    with get_connection() as conn:
        articles = [dict(r) for r in conn.execute(
            "SELECT * FROM articles ORDER BY collected_at DESC LIMIT 1000"
        ).fetchall()]
        reports = [dict(r) for r in conn.execute(
            "SELECT * FROM reports"
        ).fetchall()]
        metrics = [dict(r) for r in conn.execute(
            "SELECT * FROM monthly_metrics"
        ).fetchall()]
    
    seed_data = {"articles": articles, "reports": reports, "metrics": metrics}
    
    # Convert datetime objects to strings
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, obj):
            try:
                return str(obj)
            except:
                return super().default(obj)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(seed_data, f, indent=2, cls=DateTimeEncoder)
    
    print(f"Exported {len(articles)} articles, {len(reports)} reports, {len(metrics)} metrics")
    print(f"Saved to {output_path}")

if __name__ == '__main__':
    export_seed()
