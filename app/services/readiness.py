"""Production readiness checks that are safe to expose to operators."""
def check_configuration(config):
 required=("SECRET_KEY","SQLALCHEMY_DATABASE_URI")
 missing=[k for k in required if not config.get(k)]
 return {"ready":not missing,"missing":missing}
def check_database(db):
 try: db.session.execute(db.text("SELECT 1")); return {"ok":True}
 except Exception: return {"ok":False}
def readiness_report(config,db):
 c=check_configuration(config); d=check_database(db)
 return {"ready":c["ready"] and d["ok"],"configuration":c,"database":d}
