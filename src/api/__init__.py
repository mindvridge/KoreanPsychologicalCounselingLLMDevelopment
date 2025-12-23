"""
API 라우터 패키지
src/api.py의 app 객체를 re-export
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트 경로 찾기
_current_dir = Path(__file__).parent
_project_root = _current_dir.parent
_api_py_path = _project_root / "api.py"

# app 객체 초기화
app = None

# api.py를 직접 import
try:
    # sys.path에 프로젝트 루트 추가
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    
    # importlib을 사용하여 동적으로 로드
    import importlib.util
    
    # api.py 파일이 존재하는지 확인
    if not _api_py_path.exists():
        raise FileNotFoundError(f"API file not found: {_api_py_path}")
    
    # 모듈 spec 생성
    spec = importlib.util.spec_from_file_location("src.api.api", str(_api_py_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec from {_api_py_path}")
    
    # 모듈 로드
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    
    # app 객체 확인 및 가져오기
    if not hasattr(api_module, 'app'):
        raise AttributeError(f"Module does not have 'app' attribute")
    
    app = api_module.app
    
    # app이 None인지 확인
    if app is None:
        raise ValueError("app object is None")
    
    __all__ = ['app']
    
except Exception as e:
    # 실패 시 로깅 및 재시도
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import app from api.py: {e}")
    logger.error(f"API file path: {_api_py_path}")
    logger.error(f"API file exists: {_api_py_path.exists()}")
    
    # 상대 경로로 import 시도
    try:
        # src.api.api 모듈로 import 시도
        import importlib
        # 프로젝트 루트를 sys.path에 추가
        if str(_project_root) not in sys.path:
            sys.path.insert(0, str(_project_root))
        
        # api 모듈을 직접 import
        api_module = importlib.import_module('api')
        if hasattr(api_module, 'app') and api_module.app is not None:
            app = api_module.app
            __all__ = ['app']
            logger.info("Successfully imported app using import_module('api')")
        else:
            raise AttributeError("Module does not have 'app' attribute or app is None")
    except Exception as e2:
        logger.error(f"Alternative import method failed: {e2}")
        # 마지막 시도: src.api.api 모듈로 직접 import
        try:
            import importlib
            # src 패키지에서 api 모듈 import
            src_module = importlib.import_module('src')
            if hasattr(src_module, 'api') and hasattr(src_module.api, 'app') and src_module.api.app is not None:
                app = src_module.api.app
                __all__ = ['app']
                logger.info("Successfully imported app from src.api")
            else:
                raise AttributeError("src.api does not have 'app' attribute or app is None")
        except Exception as e3:
            logger.error(f"Final import attempt failed: {e3}")
            # app을 None으로 설정하지 않고, 에러를 발생시킴
            raise ImportError(f"Could not import app from api.py. Original error: {e}, Alternative error: {e2}, Final error: {e3}") from e3
