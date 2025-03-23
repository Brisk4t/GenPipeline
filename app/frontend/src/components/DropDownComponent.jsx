import React, { useState } from 'react';
import { FormControl, InputLabel, Select, MenuItem, Typography } from '@mui/material';

function DropDownComponent({ onSelectionChange }) {
    // Set initial selected value (can be empty or default)

    // Define the dropdown options with their related text strings
    const options = [
        { label: 'Hindi Female', value: '1qEiC6qsybMkmnNdVMbK' },
        { label: 'Hindi Male', value: 'PbLyyOzcAbfd6xduq5vt' },
        { label: 'Bhojpuri - Male', value: '3Th96YoTP1kEKxJroYo1' },
    ];

    const [selectedOption, setSelectedOption] = useState(options[0].value);

    const handleSelectChange = (event) => {
        // Update the state with the related text string when the selection changes
        const selectedValue = event.target.value;
        setSelectedOption(selectedValue);

        if (onSelectionChange) {
            onSelectionChange(selectedValue);  // Pass the selected value to the parent
        }
    };

    return (
        <div>
            <FormControl fullWidth margin="normal">
                <InputLabel id="dropdown-label">Choose a voice</InputLabel>
                <Select
                    labelId="dropdown-label"
                    value={selectedOption}
                    label="Choose an option"
                    onChange={handleSelectChange}
                >
                    {options.map((option, index) => (
                        <MenuItem key={index} value={option.value}>
                            {option.label}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
        </div>
    );
}

export default DropDownComponent;
