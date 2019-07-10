# -*- coding: utf-8 -*-

import threading


class TestAsyncThreadImport:
    def test_thread_import(self):
        def thread_func(results):
            try:
                import mygeotab

                mygeotab.API("testuser", session_id="abc123")
                results.append(None)
            except Exception as e:
                results.append(e)

        results = []
        thread = threading.Thread(target=thread_func, args=(results,))
        thread.start()
        thread.join()
        assert len(results) == 1
        assert results[0] is None
