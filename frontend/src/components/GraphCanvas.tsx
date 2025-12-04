import React, { useCallback, useEffect } from 'react';
import { ReactFlow, Background, Controls, useNodesState, useEdgesState, addEdge, type Connection } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

interface GraphCanvasProps {
    nodes: any[];
    edges: any[];
}

const GraphCanvas: React.FC<GraphCanvasProps> = ({ nodes: initialNodes, edges: initialEdges }) => {
    const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);

    useEffect(() => {
        // Transform backend data to React Flow format
        const flowNodes = initialNodes.map((n) => ({
            id: n.id,
            position: { x: Math.random() * 500, y: Math.random() * 500 }, // Random pos for MVP
            data: { label: n.label },
            type: 'default', // or custom
        }));

        const flowEdges = initialEdges.map((e, i) => ({
            id: `e-${i}`,
            source: e.source,
            target: e.target,
            label: e.relation,
            animated: true,
        }));

        setNodes(flowNodes);
        setEdges(flowEdges);
    }, [initialNodes, initialEdges, setNodes, setEdges]);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <div style={{ width: '100%', height: '100%' }}>
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                fitView
            >
                <Background color="#aaa" gap={16} />
                <Controls />
            </ReactFlow>
        </div>
    );
};

export default GraphCanvas;
