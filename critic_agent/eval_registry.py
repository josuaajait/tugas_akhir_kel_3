"""Explicit version routing; historical final-v1 APIs are never replaced."""
VERSIONS=('final-v1','final-v2')

def get_package_api(version):
    if version=='final-v1':
        from . import final_package
        return final_package
    if version=='final-v2':
        from . import eval_package_v2
        return eval_package_v2
    raise ValueError('Unsupported evaluation package: '+str(version))

def get_sandbox_api(version):
    get_package_api(version)
    if version=='final-v1':
        from . import final_sandbox
        return final_sandbox
    from . import eval_sandbox_v2
    return eval_sandbox_v2

def get_validation_api(version):
    get_package_api(version)
    if version=='final-v1':
        from . import final_validation
        return final_validation
    from . import eval_validation_v2
    return eval_validation_v2
