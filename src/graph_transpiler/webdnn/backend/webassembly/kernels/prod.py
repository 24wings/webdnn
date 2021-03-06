from typing import List

from webdnn.backend.code_generator.allocator import MemoryLayout
from webdnn.backend.code_generator.injectors.buffer_injector import BufferInjector
from webdnn.backend.code_generator.injectors.kernel_name_injector import KernelNameInjector
from webdnn.backend.webassembly.generator import WebassemblyDescriptorGenerator
from webdnn.backend.webassembly.kernel import Kernel
from webdnn.graph.operators.prod import Prod

template = """
void %%FUNC_NAME%%(const int * %%META_BUFFER%%)
{
    const float *X = %%LOAD_BUFFER(prod_X)%%;
    float *Y = %%LOAD_BUFFER(prod_Y)%%;
    const int *y_stride = %%LOAD_BUFFER(prod_y_stride)%%;
    const int *y_shape = %%LOAD_BUFFER(prod_y_shape)%%;
    const int *x_stride = %%LOAD_BUFFER(prod_x_stride)%%;
    const int D = %%LOAD_BUFFER(prod_D)%%;
    const int N = %%LOAD_BUFFER(prod_N)%%;
    const int MAX_GID = %%LOAD_BUFFER(prod_MAX_GID)%%;
    const int x_target_axis_stride = %%LOAD_BUFFER(prod_x_target_axis_stride)%%;

    for (int gid = 0; gid < MAX_GID; gid++) {
        int x_index = 0;
        for (int d = 0; d < D; d++) x_index += ((gid / y_stride[d]) % y_shape[d]) * x_stride[d];

        float y = 1.0f;
        for (int i = 0; i < N; i++) {
            const float x = X[x_index];

            y *= x;

            x_index += x_target_axis_stride;
        }

        Y[gid] = y;
    }
}
"""


@WebassemblyDescriptorGenerator.register_handler(Prod)
def prod_handler(op: Prod, memory_layout: MemoryLayout) -> List[Kernel]:
    x = op.inputs["x"]
    y = op.outputs["y"]

    axis = op.parameters["axis"]

    buffer_injector = BufferInjector()
    buffer_injector.register({
        "prod_X": memory_layout[x],
        "prod_Y": memory_layout[y],
        "prod_y_stride": y.stride,
        "prod_y_shape": y.shape,
        "prod_x_stride": [x.stride_dict[a] for a in y.order.axes],
        "prod_D": y.ndim,
        "prod_N": x.shape_dict[axis],
        "prod_MAX_GID": y.size,
        "prod_x_target_axis_stride": x.stride_dict[axis]
    })

    name_injector = KernelNameInjector(op)

    source = template
    source = buffer_injector.inject(source)
    source = name_injector.inject(source)

    kernel = Kernel(
        {name_injector.name: source},
        name_injector.name,
        buffer_injector.buffer,
        buffer_injector.unresolved_value_list
    )

    return [kernel]
