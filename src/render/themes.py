def get_theme(theme_name: str) -> str:
    if theme_name == "modern":
        return """<style>
  classDiagram {
    class {
      BackgroundColor transparent
      HeaderBackgroundColor transparent
      Shadowing 0
      FontName Arial
    }
    .added {
      BackgroundColor #D4EDDA
      LineColor #28A745
    }
    .removed {
      BackgroundColor #F8D7DA
      LineColor #DC3545
    }
    .modified {
      BackgroundColor #FFF3CD
      LineColor #FFA500
    }
    .moved {
      BackgroundColor #FFF3CD
      LineColor #FFA500
    }
    .impacted {
      BackgroundColor #F8F9FA
      LineColor #6C757D
      LineStyle 4
      FontColor #6C757D
    }
    .package_added {
      BackgroundColor #E8F5E9
      LineColor #28A745
    }
    .package_removed {
      BackgroundColor #FFEBEE
      LineColor #DC3545
    }
    .package_modified {
      BackgroundColor transparent
      LineColor #FFA500
    }
  }
</style>"""
    return ""
