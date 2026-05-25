from typing import List, Dict
from ecommerce_ops.graph.state import AgentDecision

class DigestBuilder:
    def compose_html(self, decisions: List[AgentDecision]) -> str:
        """Compose the daily digest email body."""
        autonomous = [d for d in decisions if not d.requires_approval]
        pending = [d for d in decisions if d.requires_approval]
        
        html = f"""
        <html>
            <body style='font-family: sans-serif;'>
                <h1>Daily Ops Digest 🤖</h1>
                <hr/>
                
                <h2 style='color: #2e7d32;'>✅ Actions Taken (Autonomous)</h2>
                <ul>
                    {"".join([f"<li><b>{d.agent_id}</b>: {d.reasoning}</li>" for d in autonomous]) or "<li>No autonomous actions today.</li>"}
                </ul>
                
                <h2 style='color: #d32f2f;'>⚠️ Needs Your Attention (HITL)</h2>
                <ul>
                    {"".join([f"<li><b>{d.agent_id}</b>: {d.reasoning} <a href='#'>[Approve]</a></li>" for d in pending]) or "<li>No actions pending approval.</li>"}
                </ul>
                
                <footer style='margin-top: 50px; font-size: 0.8em; color: #666;'>
                    ecommerce-ops-agent is running in shadow mode.
                </footer>
            </body>
        </html>
        """
        return html
