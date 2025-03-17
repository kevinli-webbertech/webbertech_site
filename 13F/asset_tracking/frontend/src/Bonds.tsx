import React, { useState, useEffect } from 'react';
import {
  MaterialReactTable,
  useMaterialReactTable,
  MRT_ColumnDef,
} from 'material-react-table';
import { Button, TextField, Box, Paper } from '@mui/material';

interface Bond {
  id: number;
  bond_name: string;
  bond_type: string;
  bond_term: number;
  amount: number;
  maturity_date: string;
  apy: number;
  platform: string;
  comment: string;
}

const Bonds: React.FC = () => {
  const [bonds, setBonds] = useState<Bond[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [newBond, setNewBond] = useState<Partial<Bond>>({
    bond_name: '',
    bond_type: '',
    bond_term: 0,
    amount: 0,
    maturity_date: '',
    apy: 0,
    platform: '',
    comment: '',
  });

  // ✅ Fetch Bonds
  useEffect(() => {
    fetch('http://localhost:5000/api/bonds')
      .then((response) => response.json())
      .then((data: Bond[]) => {
        setBonds(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching bonds:', err);
        setLoading(false);
      });
  }, []);

  // ✅ Add a New Bond
  const addBond = async () => {
    if (!newBond.bond_name || !newBond.amount || !newBond.bond_term) {
      alert('Please fill in all required fields');
      return;
    }

    const response = await fetch('http://localhost:5000/api/bonds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(newBond),
    });

    if (response.ok) {
      setNewBond({ bond_name: '', bond_type: '', bond_term: 0, amount: 0, maturity_date: '', apy: 0, platform: '', comment: '' });
      fetch('http://localhost:5000/api/bonds')
        .then((res) => res.json())
        .then(setBonds);
    }
  };

  // ✅ Delete Bond
  const deleteBond = async (id: number) => {
    await fetch(`http://localhost:5000/api/bonds/${id}`, { method: 'DELETE' });
    setBonds(bonds.filter((bond) => bond.id !== id));
  };

  // ✅ Table Columns (Matching SQL)
  const columns: MRT_ColumnDef<Bond>[] = [
    { accessorKey: 'bond_name', header: 'Bond Name' },
    { accessorKey: 'bond_type', header: 'Bond Type' },
    { accessorKey: 'bond_term', header: 'Bond Term' },
    { accessorKey: 'amount', header: 'Amount ($)' },
    { accessorKey: 'maturity_date', header: 'Maturity Date' },
    { accessorKey: 'apy', header: 'APY (%)' },
    { accessorKey: 'platform', header: 'Platform' },
    { accessorKey: 'comment', header: 'Comment' },
    {
      accessorKey: 'id',
      header: 'Actions',
      Cell: ({ cell }: { cell: any }) => (
        <Button variant="contained" color="secondary" onClick={() => deleteBond(cell.getValue() as number)}>
          Delete
        </Button>
      ),
    },
  ];

  return (
    <Paper sx={{ padding: '20px' }}>
      <h2>Bonds</h2>

      {/* ✅ Input Fields (Keep SQL Structure) */}
      <Box sx={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
        <TextField label="Bond Name" value={newBond.bond_name} onChange={(e) => setNewBond({ ...newBond, bond_name: e.target.value })} />
        <TextField label="Bond Type" value={newBond.bond_type} onChange={(e) => setNewBond({ ...newBond, bond_type: e.target.value })} />
        <TextField label="Bond Term" type="number" value={newBond.bond_term} onChange={(e) => setNewBond({ ...newBond, bond_term: Number(e.target.value) })} />
        <TextField label="Amount ($)" type="number" value={newBond.amount} onChange={(e) => setNewBond({ ...newBond, amount: Number(e.target.value) })} />
        <Button variant="contained" color="primary" onClick={addBond}>Add Bond</Button>
      </Box>

      {/* ✅ Table Display */}
      <MaterialReactTable columns={columns} data={bonds} state={{ isLoading: loading }} />
    </Paper>
  );
};

export default Bonds;
