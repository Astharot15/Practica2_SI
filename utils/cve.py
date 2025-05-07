import json
import requests as request

def last_ten_cve(maxcves=0):
    res = request.get("http://cve.circl.lu/api/last")
    if res.status_code == 200:
      reply = json.loads(res.content)
      cves = list()
      for node in reply:
        if "REJECT" not in node["summary"]:
          cves.append(node["id"])
      return {
        "success": True,
        "requesturl": res.url,
        "cves": cves if maxcves == 0 else cves[:maxcves]
      }
    return {
      "success": False,
      "reason": "expected HTTP 200 status code but got %d instead for requesturl" % (res.status_code)
    }
  
print(last_ten_cve(5))