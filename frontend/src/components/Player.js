const Player = ({ name, chips }) => {
    return (
      <div className="bg-blue-700 text-white p-4 rounded shadow">
        <h3 className="text-lg font-bold">{name}</h3>
        <p>Chips: {chips}</p>
      </div>
    );
  };
  
  export default Player;
  