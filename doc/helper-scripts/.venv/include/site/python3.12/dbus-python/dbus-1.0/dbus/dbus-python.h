/* C API for _dbus_bindings, used by _dbus_glib_bindings and any third-party
 * main loop integration which might happen in future.
 *
 * This file is currently Python-version-independent - please keep it that way.
 *
 * Copyright (C) 2006 Collabora Ltd. <http://www.collabora.co.uk/>
 *
 * SPDX-License-Identifier: MIT
 *
 * Permission is hereby granted, free of charge, to any person
 * obtaining a copy of this software and associated documentation
 * files (the "Software"), to deal in the Software without
 * restriction, including without limitation the rights to use, copy,
 * modify, merge, publish, distribute, sublicense, and/or sell copies
 * of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 * HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 */

#ifndef DBUS_PYTHON_H
#define DBUS_PYTHON_H

#include <Python.h>
#include <dbus/dbus.h>

#define PYDBUS_CAPSULE_NAME "_dbus_bindings._C_API"

DBUS_BEGIN_DECLS

typedef void (*_dbus_py_func_ptr)(void);

typedef dbus_bool_t (*_dbus_py_conn_setup_func)(DBusConnection *, void *);
typedef dbus_bool_t (*_dbus_py_srv_setup_func)(DBusServer *, void *);
typedef void (*_dbus_py_free_func)(void *);

#define DBUS_BINDINGS_API_COUNT 3

#ifdef INSIDE_DBUS_PYTHON_BINDINGS

extern DBusConnection *DBusPyConnection_BorrowDBusConnection(PyObject *);
extern PyObject *DBusPyNativeMainLoop_New4(_dbus_py_conn_setup_func,
                                           _dbus_py_srv_setup_func,
                                           _dbus_py_free_func,
                                           void *);

#else

static PyObject *_dbus_bindings_module = NULL;
static _dbus_py_func_ptr *dbus_bindings_API;

#define DBusPyConnection_BorrowDBusConnection \
        (*(DBusConnection *(*)(PyObject *))dbus_bindings_API[1])
#define DBusPyNativeMainLoop_New4 \
    ((PyObject *(*)(_dbus_py_conn_setup_func, _dbus_py_srv_setup_func, \
                    _dbus_py_free_func, void *))dbus_bindings_API[2])

static int
import_dbus_bindings(const char *this_module_name)
{
    PyObject *c_api;
    int count;

    _dbus_bindings_module = PyImport_ImportModule("_dbus_bindings");
    if (!_dbus_bindings_module) {
        return -1;
    }
    c_api = PyObject_GetAttrString(_dbus_bindings_module, "_C_API");
    if (c_api == NULL) return -1;
    dbus_bindings_API = NULL;
    if (PyCapsule_IsValid(c_api, PYDBUS_CAPSULE_NAME)) {
        dbus_bindings_API = (_dbus_py_func_ptr *)PyCapsule_GetPointer(
            c_api, PYDBUS_CAPSULE_NAME);
    }
    Py_CLEAR(c_api);
    if (!dbus_bindings_API) {
        PyErr_SetString(PyExc_RuntimeError, "C API is not a PyCapsule");
        return -1;
    }
    count = *(int *)dbus_bindings_API[0];
    if (count < DBUS_BINDINGS_API_COUNT) {
        PyErr_Format(PyExc_RuntimeError,
                     "_dbus_bindings has API version %d but %s needs "
                     "_dbus_bindings API version at least %d",
                     count, this_module_name,
                     DBUS_BINDINGS_API_COUNT);
        return -1;
    }
    return 0;
}

#endif

DBUS_END_DECLS

#endif
