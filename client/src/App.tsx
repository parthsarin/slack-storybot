import React, { FunctionComponent, useState } from 'react';
import './App.css';
import Authenticate from './Authenticate';

const App: FunctionComponent<{}> = () => {
    // Get the slack name from local storage if it exists there
    const [slackName, setSlackName] = useState<string | null>(
        localStorage.getItem("slackName")
    );

    if (slackName) {
        // Authenticated
        return (
            <span>Authenticated as @{ slackName }</span>
        );
    } else {
        // Not authenticated yet
        return (
        <Authenticate 
            onSubmit={
                (newUsername) => {
                    setSlackName(newUsername);
                    localStorage.setItem('slackName', newUsername);
                }
            }
            newUser={true}
        />
        )
    }
}

export default App;
