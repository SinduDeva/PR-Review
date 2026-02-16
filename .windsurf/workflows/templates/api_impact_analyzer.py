#!/usr/bin/env python3
"""
API Impact Analyzer for PR Code Review
Analyzes all APIs impacted by code changes in the PR.
"""

import json
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path


class APIImpactAnalyzer:
    """Analyzes API impacts from code changes"""

    # REST endpoint patterns
    REST_ENDPOINT_PATTERNS = [
        r'@(?:Get|Post|Put|Delete|Patch|Request)Mapping\s*\(\s*["\']([^"\']+)',
        r'@RequestMapping\s*\(\s*(?:path|value)\s*=\s*["\']([^"\']+)',
        r'@(?:GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\s*\(\s*["\']([^"\']+)',
    ]

    # HTTP method detection patterns
    HTTP_METHOD_PATTERNS = {
        'GET': [r'@GetMapping', r'@RequestMapping\s*\(\s*method\s*=\s*RequestMethod\.GET'],
        'POST': [r'@PostMapping', r'@RequestMapping\s*\(\s*method\s*=\s*RequestMethod\.POST'],
        'PUT': [r'@PutMapping', r'@RequestMapping\s*\(\s*method\s*=\s*RequestMethod\.PUT'],
        'DELETE': [r'@DeleteMapping', r'@RequestMapping\s*\(\s*method\s*=\s*RequestMethod\.DELETE'],
        'PATCH': [r'@PatchMapping', r'@RequestMapping\s*\(\s*method\s*=\s*RequestMethod\.PATCH'],
    }

    # API versioning patterns
    VERSION_PATTERNS = [
        r'/v\d+',
        r'/api/v\d+',
        r'api-version',
        r'Accept.*version',
    ]

    @staticmethod
    def extract_endpoints_from_diff(diff_content: str) -> List[Dict]:
        """Extract API endpoints from diff content"""
        endpoints = []
        lines = diff_content.split('\n')

        for i, line in enumerate(lines):
            # Look for endpoint definitions
            for pattern in APIImpactAnalyzer.REST_ENDPOINT_PATTERNS:
                matches = re.finditer(pattern, line)
                for match in matches:
                    endpoint_path = match.group(1) if match.groups() else None
                    if endpoint_path:
                        # Determine HTTP method
                        method = 'UNKNOWN'
                        context = '\n'.join(lines[max(0, i-5):i+5])
                        for http_method, patterns in APIImpactAnalyzer.HTTP_METHOD_PATTERNS.items():
                            for method_pattern in patterns:
                                if re.search(method_pattern, context):
                                    method = http_method
                                    break

                        endpoints.append({
                            'path': endpoint_path,
                            'method': method,
                            'line': i + 1,
                            'type': 'ENDPOINT'
                        })

        return endpoints

    @staticmethod
    def detect_breaking_changes(
        old_endpoints: List[Dict],
        new_endpoints: List[Dict],
        diff_content: str
    ) -> Tuple[List[Dict], List[str]]:
        """Detect breaking API changes"""
        breaking_changes = []
        warnings = []

        # Check for removed endpoints
        old_paths = {(e.get('method'), e.get('path')) for e in old_endpoints}
        new_paths = {(e.get('method'), e.get('path')) for e in new_endpoints}

        removed = old_paths - new_paths
        for method, path in removed:
            breaking_changes.append({
                'endpoint': f'{method} {path}',
                'type': 'BREAKING',
                'change': f'Endpoint removed: {method} {path}',
                'impact': 'HIGH',
                'backward_compatible': False,
                'affected_consumers': [],
                'migration_notes': 'This endpoint is no longer available. Clients must migrate to alternative endpoints.'
            })

        # Check for parameter changes
        param_patterns = [
            r'@RequestParam\s*\(\s*["\'](\w+)',
            r'@PathVariable\s*\(\s*["\'](\w+)',
            r'@RequestBody',
        ]

        for pattern in param_patterns:
            old_params = set(re.findall(pattern, '\n'.join(old_endpoints)))
            new_params = set(re.findall(pattern, '\n'.join(new_endpoints)))

            if old_params != new_params:
                removed_params = old_params - new_params
                if removed_params:
                    warnings.append(f'Required parameters may have changed. Check migration path.')
                    breaking_changes.append({
                        'endpoint': 'Multiple endpoints',
                        'type': 'BREAKING',
                        'change': f'Parameter(s) changed: {", ".join(removed_params)}',
                        'impact': 'HIGH',
                        'backward_compatible': False,
                        'affected_consumers': [],
                        'migration_notes': 'API parameters have been modified. Ensure all clients are updated.'
                    })

        # Check for response type changes
        if '+json' in diff_content or 'produces = {"application/json"}' in diff_content:
            warnings.append('Response type may have changed - verify backward compatibility')

        return breaking_changes, warnings

    @staticmethod
    def analyze_api_impact_from_files(
        files_changed: List[Dict],
        file_diffs: Dict[str, str]
    ) -> Dict:
        """Analyze API impacts from changed files"""
        impact_analysis = {
            'affected_apis': [],
            'breaking_changes': [],
            'new_endpoints': [],
            'modified_endpoints': [],
            'removed_endpoints': [],
            'affected_consumers': [],
            'warnings': []
        }

        # Scan for controller/API files
        controller_files = [f for f in files_changed if 'controller' in f.get('path', '').lower()]
        dto_files = [f for f in files_changed if 'dto' in f.get('path', '').lower()]
        api_files = controller_files + dto_files

        if not api_files:
            return impact_analysis

        # Analyze each API file
        for file_info in api_files:
            file_path = file_info.get('path', '')
            diff_content = file_diffs.get(file_path, '')

            # Extract endpoints from changes
            endpoints = APIImpactAnalyzer.extract_endpoints_from_diff(diff_content)

            if endpoints:
                impact_analysis['affected_apis'].extend(endpoints)

                # Detect changes
                for endpoint in endpoints:
                    if '+' in diff_content and endpoint['path'] in diff_content:
                        # Check if it's a new endpoint
                        if '@@' in diff_content:
                            impact_analysis['new_endpoints'].append(endpoint)
                    else:
                        impact_analysis['modified_endpoints'].append(endpoint)

        # Consolidate findings
        if impact_analysis['affected_apis']:
            impact_analysis['breaking_changes'], warnings = APIImpactAnalyzer.detect_breaking_changes(
                [],
                impact_analysis['affected_apis'],
                ''.join(file_diffs.values())
            )
            impact_analysis['warnings'].extend(warnings)

        return impact_analysis

    @staticmethod
    def generate_api_summary(impact_data: Dict) -> Dict:
        """Generate summary of API impacts"""
        return {
            'total_affected_apis': len(impact_data.get('affected_apis', [])),
            'total_breaking_changes': len(impact_data.get('breaking_changes', [])),
            'total_new_endpoints': len(impact_data.get('new_endpoints', [])),
            'total_modified_endpoints': len(impact_data.get('modified_endpoints', [])),
            'total_removed_endpoints': len(impact_data.get('removed_endpoints', [])),
            'has_breaking_changes': len(impact_data.get('breaking_changes', [])) > 0,
            'migration_required': len(impact_data.get('breaking_changes', [])) > 0,
            'warnings': impact_data.get('warnings', [])
        }


def integrate_api_impact_into_jira(jira_comment: str, impact_data: Dict) -> str:
    """
    Integrate API impact analysis into JIRA comment.

    Returns:
        Enhanced JIRA comment with API impact section
    """
    if not impact_data.get('affected_apis'):
        return jira_comment

    api_section = []
    api_section.append("h3. 🔗 Affected APIs")
    api_section.append("")

    affected_apis = impact_data.get('affected_apis', [])
    if affected_apis:
        api_section.append("|| Endpoint || Method || Impact ||")
        for api in affected_apis[:10]:  # Show top 10
            endpoint = api.get('path', 'Unknown')
            method = api.get('method', 'UNKNOWN')
            api_section.append(f"| {{{{monospace}}}}{endpoint}{{{{monospace}}}} | {method} | API Change |")

        if len(affected_apis) > 10:
            api_section.append(f"| ... and {len(affected_apis) - 10} more | | |")

        api_section.append("")

    # Add breaking changes section if any
    breaking_changes = impact_data.get('breaking_changes', [])
    if breaking_changes:
        api_section.append("h4. ⚠️ Breaking Changes")
        api_section.append("{warning}The following breaking changes require consumer migration:{warning}")
        api_section.append("")

        for change in breaking_changes:
            api_section.append(f"* {{{{monospace}}}}{change.get('endpoint', 'Unknown')}{{{{monospace}}}}")
            api_section.append(f"  - {change.get('change', '')}")
            api_section.append(f"  - Impact: {{color:red}}{change.get('impact', 'Unknown')}{{color}}")

        api_section.append("")

    # Insert before recommendations section
    if "h3. ✅ Recommendation" in jira_comment:
        position = jira_comment.find("h3. ✅ Recommendation")
        return jira_comment[:position] + "\n".join(api_section) + "\n----\n\n" + jira_comment[position:]
    else:
        return jira_comment + "\n".join(api_section)


def main():
    """Command-line interface for API impact analysis"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python api_impact_analyzer.py <review-data.json>")
        sys.exit(1)

    data_file = sys.argv[1]

    try:
        with open(data_file, 'r') as f:
            data = json.load(f)

        # Extract file diffs
        file_diffs = {}
        for file_info in data.get('files_reviewed', []):
            file_path = file_info.get('path', '')
            diff = file_info.get('diff', '')
            if diff:
                file_diffs[file_path] = diff

        # Analyze API impacts
        analyzer = APIImpactAnalyzer()
        impact_analysis = analyzer.analyze_api_impact_from_files(
            data.get('files_reviewed', []),
            file_diffs
        )

        # Generate summary
        summary = analyzer.generate_api_summary(impact_analysis)

        # Output results
        print("📊 API Impact Analysis Summary:")
        print(f"  Total Affected APIs: {summary['total_affected_apis']}")
        print(f"  Breaking Changes: {summary['total_breaking_changes']}")
        print(f"  New Endpoints: {summary['total_new_endpoints']}")
        print(f"  Modified Endpoints: {summary['total_modified_endpoints']}")

        if summary['has_breaking_changes']:
            print("\n⚠️ WARNING: Breaking changes detected")
            print("   Migration required for API consumers")

        # Save analysis
        output_file = data_file.replace('.json', '-api-impact.json')
        with open(output_file, 'w') as f:
            json.dump(impact_analysis, f, indent=2)

        print(f"\n✅ API impact analysis saved: {output_file}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
