param(
  [switch]$Fix
)

$argsList = @("check", "src", "main.py", "scripts")
if ($Fix) {
  $argsList += "--fix"
}

ruff @argsList
